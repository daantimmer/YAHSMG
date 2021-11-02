import re
import pprint
import jinja2
from jinja2.runtime import V


def replace_non_ascii(text: str) -> str:
    if text:
        return re.sub("[^0-9a-zA-Z]+", "_", text.strip())
    return text


# matches:
# @startuml state name will be derived from here
start_diagram_regex = re.compile(r"@startuml (.*)")


def parse_start_diagram(match: re.match) -> str:
    return replace_non_ascii(match.group(1))


# matches:
# @enduml
end_diagram_regex = re.compile(r"@enduml")

# matches:
# state_name <-> state_name : event_name
# state_name <-> state_name : event_name [condition]
# state_name <-> state_name : event_name / event_action
# state_name <-> state_name : event_name [condition] / event_action
event_regex = re.compile(
    r"(\w+) +(<-\w*-*|-*\w*->) +([\w]+|\[\*\])(?: +: +([\w][\w ]+[\w])(?: +\[([\w ]+)\])?(?: +\/ *([\w ]+))?)"
)


def parse_event(match: re.match) -> dict:
    source = match.group(1)
    direction = match.group(2)
    target = match.group(3)

    if direction.startswith("<-"):
        source, target = target, source

    return {
        "source": source,
        "target": target,
        "event": replace_non_ascii(match.group(4)),
        "condition": replace_non_ascii(match.group(5)),
        "action": replace_non_ascii(match.group(6))
    }


# matches:
# [*] -> state_name
# state_name <- [*]
init_regex = re.compile(r"([\w]+) +<-\w*-* \[\*\]|\[\*\] -*\w*-> +([\w]+)")


def parse_init(match: re.match) -> str:
    target1 = match.group(1)
    target2 = match.group(2)

    return target1 if target1 else target2


# matches:
# state short_name
# state short_name as "long name"                   (long name is ignored)
# state "long name" as short_name                   (long name is ignored)
# state short_name : ""description""                (description is ignored)
# state short_name as "long name" : ""description"" (description and long name is ignored)
# state "long name" as short_name : ""description"" (description and long name is ignored)
# state short_name {
# state short_name as "long name" {                 (long name is ignored)
# state "long name" as short_name {                 (long name is ignored)
state_regex = re.compile(
    r"state +(?:\"[\w\d ]+\"|([\w\d]+))(?: +as (?:\"[\w\d ]+\"|([\w\d]+)))?(?: *({))?"
)


def parse_state(match: re.match) -> dict:
    short_name_1 = match.group(1)
    short_name_2 = match.group(2)
    is_composite_state = True if match.group(3) else False
    return {
        "name": short_name_1 if short_name_1 else short_name_2,
        "composite": is_composite_state
    }


composite_state_end_regex = re.compile(r"(})")

# matches:
# state_name : EntryExit / entry_exit_action
# state_name : entryexit / entry_exit_action
# state_name : any words before entryexit / entry_exit_action
state_action_regex = re.compile(
    r"([\w\d]+) *: *[\w\d ]+([Ee](?:ntry|xit)) *\/ *([\w\d ]+)")


def parse_state_action(match: re.match) -> dict:
    return {
        "name": match.group(1),
        "entry_exit": match.group(2).lower(),
        "action": replace_non_ascii(match.group(3))
    }


state_inner_action_regex = re.compile(
    r"([\w\d]+) *: *([\w\s]+)(?: +\[([\w ]+)\])? +\/ *([\w\d ]+)")


def parse_state_inner_action(match: re.match) -> dict:
    return {
        "source": match.group(1),
        "target": None,
        "event": replace_non_ascii(match.group(2)),
        "condition": replace_non_ascii(match.group(3)),
        "action": replace_non_ascii(match.group(4))
    }


class StateObject:
    def __init__(self, name):
        self.state_stack = ["Top"]

        self.state_set = set()
        self.event_set = set()
        self.state_parent = {}
        self.state_childs = {"Top": set()}

        self.parsed = {
            "states": [],
            "state_parents": {},
            "state_actions": {
                "entry": {},
                "exit": {}
            },
            "is_leaf_state": {},
            "allEvents": set(),
            "allActions": set(),
            "allConditions": set(),
            "events": {},
            "inits": {},
            "name": name
        }

    def handleState(self, state: str) -> None:
        self.state_set.add(state)
        if state not in self.state_parent:
            self.state_parent[state] = self.state_stack[-1]
            self.state_childs[state] = set()
        elif self.state_parent[
                state] == "Top" and self.state_stack[-1] != "Top":
            self.state_parent[state] = self.state_stack[-1]

        self.state_childs[self.state_stack[-1]].add(state)


def parse_data(data) -> list:
    diagrams = []
    state_object = None

    if isinstance(data, str):
        data = data.splitlines()

    for line in data:
        line = line.strip()
        match = start_diagram_regex.match(line)
        if match:
            state_object = StateObject(parse_start_diagram(match))
            continue

        if state_object is None:
            continue

        match = end_diagram_regex.match(line)
        if match:
            state_object.parsed["states"] = sorted(list(
                state_object.state_set))
            state_object.parsed["state_parents"] = state_object.state_parent

            state_object.parsed["depth"] = {}

            for state in state_object.state_parent.keys():
                state_object.parsed["depth"][state] = 0

                key = state
                while state_object.state_parent[key] != "Top":
                    state_object.parsed["depth"][state] += 1
                    key = state_object.state_parent[key]

            inv_depth = {}
            for k, v in state_object.parsed["depth"].items():
                inv_depth[v] = inv_depth.get(v, []) + [k]

            for v in inv_depth.values():
                v.sort()
            state_object.parsed["depth"] = inv_depth

            if None in state_object.parsed["allEvents"]:
                state_object.parsed["allEvents"].remove(None)
            state_object.parsed["allEvents"] = sorted(
                list(state_object.parsed["allEvents"]))

            if None in state_object.parsed["allActions"]:
                state_object.parsed["allActions"].remove(None)
            state_object.parsed["allActions"] = sorted(
                list(state_object.parsed["allActions"]))

            if None in state_object.parsed["allConditions"]:
                state_object.parsed["allConditions"].remove(None)
            state_object.parsed["allConditions"] = sorted(
                list(state_object.parsed["allConditions"]))

            state_object.parsed["is_leaf_state"] = {
                k: len(v) == 0
                for k, v in state_object.state_childs.items()
            }

            diagrams.append(state_object.parsed)
            state_object = None
            continue

        match = event_regex.match(line)
        if match:
            event = parse_event(match)

            if not event["source"] in state_object.parsed["events"]:
                state_object.parsed["events"][event["source"]] = []

            state_object.parsed["events"][event["source"]].append(event)
            state_object.parsed["allActions"].add(event["action"])
            state_object.parsed["allConditions"].add(event["condition"])
            state_object.parsed["allEvents"].add(event["event"])

            state_object.handleState(event["source"])
            state_object.handleState(event["target"])
            continue

        match = init_regex.match(line)
        if match:
            init = parse_init(match)
            state_object.parsed["inits"][state_object.state_stack[-1]] = init
            state_object.handleState(init)
            continue

        match = state_regex.match(line)
        if match:
            state = parse_state(match)
            state_object.handleState(state["name"])
            if state["composite"]:
                state_object.state_stack.append(state["name"])
            continue

        match = composite_state_end_regex.match(line)
        if match:
            state_object.state_stack.pop()
            continue

        match = state_action_regex.match(line)
        if match:
            state_action = parse_state_action(match)

            if state_action["name"] not in state_object.parsed[
                    "state_actions"][state_action["entry_exit"]]:
                state_object.parsed["state_actions"][
                    state_action["entry_exit"]][state_action["name"]] = []

            state_object.parsed["state_actions"][state_action["entry_exit"]][
                state_action["name"]].append(state_action["action"])

            state_object.parsed["allActions"].add(state_action["action"])

            state_object.handleState(state_action["name"])
            continue

        match = state_inner_action_regex.match(line)
        if match:
            state_inner_action = parse_state_inner_action(match)

            if not state_inner_action["source"] in state_object.parsed[
                    "events"]:
                state_object.parsed["events"][
                    state_inner_action["source"]] = []

            state_object.parsed["events"][state_inner_action["source"]].append(
                state_inner_action)
            state_object.parsed["allActions"].add(state_inner_action["action"])
            state_object.parsed["allConditions"].add(
                state_inner_action["condition"])
            state_object.parsed["allEvents"].add(state_inner_action["event"])

            state_object.handleState(state_inner_action["source"])
            continue

        if line:
            print(f"Unparsed line: {line}")

    return diagrams
