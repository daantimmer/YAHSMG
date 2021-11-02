#ifndef HSM_HPP
#define HSM_HPP

#include <cstddef>
#include <cstdint>
#include <type_traits>

// This code is from:
// Yet Another Hierarchical State Machine
// by Stefan Heinzmann
// Overload issue 64 december 2004
// http://www.state-machine.com/resources/Heinzmann04.pdf

/* This is a basic implementation of UML Statecharts.
 * The key observation is that the machine can only
 * be in a leaf state at any given time. The composite
 * states are only traversed, never final.
 * Only the leaf states are ever instantiated. The composite
 * states are only mechanisms used to generate code. They are
 * never instantiated.
 */

// Top State, Composite State and Leaf State

template <typename H>
struct TopState
{
    using Host = H;
    using Base = void;

    virtual void handler(Host&) const = 0;
    virtual const char* getState() const = 0;
};

template <typename H, std::size_t id, typename B>
struct CompState;

template <typename H, std::size_t id, typename B = CompState<H, 0, TopState<H>>>
struct CompState: B
{
    using Base = B;
    using This = CompState<H, id, Base>;

    template <typename X>
    void handle(H& h, const X& x) const
    {
        Base::handle(h, x);
    }

    static void init(H&); // no implementation

    static void entry(H&)
    {}

    static void exit(H&)
    {}
};

template <typename H>
struct CompState<H, 0, TopState<H>>: TopState<H>
{
    using Base = TopState<H>;
    using This = CompState<H, 0, Base>;

    template <typename X>
    void handle(H&, const X&) const
    {}

    static void init(H&); // no implementation

    static void entry(H&)
    {}

    static void exit(H&)
    {}
};

template <typename H, std::size_t id, typename B = CompState<H, 0, TopState<H>>>
struct LeafState: B
{
    using Host = H;
    using Base = B;
    using This = LeafState<H, id, Base>;

    template <typename X>
    void handle(H& h, const X& x) const
    {
        Base::handle(h, x);
    }

    void handler(H& h) const override
    {
        handle(h, *this);
    }

    const char* getState() const override;

    static void init(H& h)
    {
        h.next(obj);
    } // don't specialize this

    static void entry(H&)
    {}

    static void exit(H&)
    {}

    static const LeafState obj; // only the leaf states have instances
};

template <typename H, std::size_t id, typename B>
const LeafState<H, id, B> LeafState<H, id, B>::obj;

// Transition Object

template <typename C, typename S, typename T>
// Current, Source, Target
struct Tran
{
    using Host = typename C::Host;
    using CurrentBase = typename C::Base;
    using SourceBase = typename S::Base;
    using TargetBase = typename T::Base;

    static constexpr bool isCB_TB = std::is_base_of_v<CurrentBase, TargetBase>;
    static constexpr bool isCB_S = std::is_base_of_v<CurrentBase, S>;
    static constexpr bool isC_S = std::is_base_of_v<C, S>;
    static constexpr bool isS_C = std::is_base_of_v<S, C>;

    static constexpr bool isExitStop = isCB_TB && isC_S;
    static constexpr bool isEntryStop = isC_S || (isCB_S && !isS_C);

    Tran(Host& h)
        : host_(h)
    {
        exitActions(host_, std::false_type{});
    }

    Tran(Host& h, void (Host::*func)())
        : host_(h)
    {
        exitActions(host_, std::false_type{});
        (h.*func)();
    }

    ~Tran()
    {
        Tran<T, S, T>::entryActions(host_, std::false_type{});
        T::init(host_);
    }

    // We use overloading to stop recursion.
    // The more natural template specialization
    // method would require to specialize the inner
    // template without specializing the outer one,
    // which is forbidden.
    static void exitActions(Host&, std::true_type)
    {}

    static void exitActions(Host& h, std::false_type)
    {
        C::exit(h);
        Tran<CurrentBase, S, T>::exitActions(h, std::bool_constant<isExitStop>{});
    }

    static void entryActions(Host&, std::true_type)
    {}

    static void entryActions(Host& h, std::false_type)
    {
        Tran<CurrentBase, S, T>::entryActions(h, std::bool_constant<isEntryStop>{});
        C::entry(h);
    }

private:
    Host& host_;
};

// Initializer for Compound States

template <typename T>
struct Init
{
    using Host = typename T::Host;

    Init(Host& h)
        : host_(h)
    {}

    ~Init()
    {
        T::entry(host_);
        T::init(host_);
    }

private:
    Host& host_;
};

#endif // HSM_HPP
