import unittest
import core.stateparser as stateparser
import pprint


def hppdiagram(input, name):
    return f"""#ifndef __cplusplus
#define __cplusplus

@startuml {name}
{input}
@enduml

class Foo {{
    int bar;
}};

class State {{
    int foo;
}};

class state{{
    int foo;
}};"""


def hppdiagram_multi(input1, name1, input2, name2):
    return f"""#ifndef __cplusplus
#define __cplusplus

/*
@startuml {name1}
{input1}
@enduml
*/

class Foo {{
    int bar;
}};

class State {{
    int foo;
}};

/*
@startuml {name2}
{input2}
@enduml
*/

class state{{
    int foo;
}};"""


def plantumldiagram(input, name):
    return f"""@startuml {name}
{input}
@enduml"""


def plantumldiagram_multi(input1, name1, input2, name2):
    return f"""@startuml {name1}
{input1}
@enduml

@startuml {name2}
{input2}
@enduml
"""


class TestGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.expected = None
        self.result = None

    def tearDown(self) -> None:
        self.stateparser = None

        for result, expected in zip(self.result, self.expected):
            self.assertEqual(result, result | expected)

    def test_empty_input(self):
        diag = plantumldiagram("", "hsm state name")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "hsm_state_name",
            "states": [],
            "allEvents": [],
            "allActions": [],
            "allConditions": []
        }]

    def test_single_state(self):
        diag = plantumldiagram("state A", "single state")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "single_state",
            "states": ["A"],
            "allEvents": [],
            "allActions": [],
            "allConditions": []
        }]

    def test_single_action(self):
        diag = plantumldiagram("""A -> B : name / action""", "single action")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "single_action",
            "states": ["A", "B"],
            "allEvents": ["name"],
            "allActions": ["action"],
            "events": {
                "A": [{
                    "action": "action",
                    "condition": None,
                    "event": "name",
                    "source": "A",
                    "target": "B"
                }]
            }
        }]

    def test_single_action_with_condition(self):
        diag = plantumldiagram("""A -> B : name [a condition]""",
                               "single action condition")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "single_action_condition",
            "states": ["A", "B"],
            "allEvents": ["name"],
            "allActions": [],
            "allConditions": ["a_condition"],
            "events": {
                "A": [{
                    "action": None,
                    "condition": "a_condition",
                    "event": "name",
                    "source": "A",
                    "target": "B"
                }]
            }
        }]

    def test_single_action_with_condition_action(self):
        diag = plantumldiagram("""A -> B : name [a condition] / an action""",
                               "single action condition action")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "single_action_condition_action",
            "states": ["A", "B"],
            "allEvents": ["name"],
            "allActions": ["an_action"],
            "allConditions": ["a_condition"],
            "events": {
                "A": [{
                    "action": "an_action",
                    "condition": "a_condition",
                    "event": "name",
                    "source": "A",
                    "target": "B"
                }]
            }
        }]

    def test_single_action_reverse(self):
        diag = plantumldiagram("""A <- B : namereverse""",
                               "single action reverse")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "single_action_reverse",
            "states": ["A", "B"],
            "allEvents": ["namereverse"],
            "allActions": [],
            "events": {
                "B": [{
                    "action": None,
                    "condition": None,
                    "event": "namereverse",
                    "source": "B",
                    "target": "A"
                }]
            }
        }]

    def test_single_init(self):
        diag = plantumldiagram("""[*] -> Ainit""", "single_init")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "single_init",
            "states": ["Ainit"],
            "inits": {
                "Top": "Ainit"
            }
        }]

    def test_single_init_reverse(self):
        diag = plantumldiagram("""AinitReverse <- [*]""",
                               "single init reverse")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "single_init_reverse",
            "states": ["AinitReverse"],
            "inits": {
                "Top": "AinitReverse"
            }
        }]

    def test_entry_action(self):
        diag = plantumldiagram("""StateAction : entry / action name""",
                               "entry action")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "entry_action",
            "states": ["StateAction"],
            "state_actions": {
                "entry": {
                    "StateAction": ["action_name"]
                },
                "exit": {}
            }
        }]

    def test_exit_action(self):
        diag = plantumldiagram("""StateAction : exit / action name""",
                               "exit action")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "exit_action",
            "states": ["StateAction"],
            "state_actions": {
                "entry": {},
                "exit": {
                    "StateAction": ["action_name"]
                }
            }
        }]

    def test_parent_leaf(self):
        diag = plantumldiagram(
            """state ParentState{
    [*] -> LeafState
}
[*] -> ParentState""", "parent leaf")

        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "parent_leaf",
            "states": ["LeafState", "ParentState"],
            "depth": {
                0: ["ParentState"],
                1: ["LeafState"]
            },
            "inits": {
                "ParentState": "LeafState",
                "Top": "ParentState"
            },
            "is_leaf_state": {
                "LeafState": True,
                "ParentState": False,
                "Top": False
            },
            "state_parents": {
                "LeafState": "ParentState",
                "ParentState": "Top"
            }
        }]

    def test_multi_diagram(self):
        diag = plantumldiagram_multi("[*] -> StateA", "diagramA",
                                     "[*] -> StateB", "diagramB")

        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "states": ["StateA"],
            "name": "diagramA"
        }, {
            "states": ["StateB"],
            "name": "diagramB"
        }]

    def test_diagram_in_cppheader(self):
        diag = hppdiagram("[*] -> StateA", "diagramA")

        self.result = stateparser.parse_data(diag)
        self.expected = [{"states": ["StateA"], "name": "diagramA"}]

    def test_diagram_in_cppheader_multi(self):
        diag = hppdiagram_multi("[*] -> StateA", "diagramA", "[*] -> StateB",
                                "diagramB")

        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "states": ["StateA"],
            "name": "diagramA"
        }, {
            "states": ["StateB"],
            "name": "diagramB"
        }]

    def test_inner_event_action(self):
        diag = plantumldiagram_multi(
            """StateName : an event name / an action name""",
            "inner event action",
            """StateName : an event name [an event condition] / an action name""",
            "inner event action condition")
        self.result = stateparser.parse_data(diag)
        self.expected = [{
            "name": "inner_event_action",
            "states": ["StateName"],
            "state_actions": {
                "entry": {},
                "exit": {}
            },
            "allEvents": ["an_event_name"],
            "allActions": ["an_action_name"],
            "events": {
                "StateName": [{
                    "action": "an_action_name",
                    "condition": None,
                    "event": "an_event_name",
                    "source": "StateName",
                    "target": None
                }]
            }
        }, {
            "name": "inner_event_action_condition",
            "states": ["StateName"],
            "state_actions": {
                "entry": {},
                "exit": {}
            },
            "allConditions": ["an_event_condition"],
            "allEvents": ["an_event_name"],
            "allActions": ["an_action_name"],
            "events": {
                "StateName": [{
                    "action": "an_action_name",
                    "condition": "an_event_condition",
                    "event": "an_event_name",
                    "source": "StateName",
                    "target": None
                }]
            }
        }]

    def test_random(self):
        diag = plantumldiagram(
            """scale 600 width

[*] -> State1
State1 --> State2 : Succeeded [Condition goes HeRe] /ActionAG fds
State1 --> End : Aborted
State1 : Entry / do something
State1 : Entry / do something else
State1 : Exit / DoNothing
State2 --> State3 : Succeeded
State2 --> End : Aborted
state State3 {
  state "Accumulate Enough Data Long State Name" as long1
  long1 : Just a test
  [*] --> long1
  long1 --> long1 : New Data
  long1 --> ProcessData : Enough Data

  state ProcessData {
    [*] --> ExecData
    ExecData -> Finished : Done
  }
}
State3 : Entry / test
State3 : Exit / detest
State3 : testevent / detest1
State3 : testeventcnd [somecond] / adetest2
State3 --> State3 : Failed
State3 --> End : Succeeded / Save Result
State3 --> End : Aborted""", "inner event action")
        self.result = stateparser.parse_data(diag)
        self.expected = [{}]


if __name__ == '__main__':
    unittest.main()