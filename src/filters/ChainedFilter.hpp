#pragma once

#include "./Common.hpp"

template<class Filter1, class Filter2>
class ChainedFilter {
private:
    Filter1 filter1_;
    Filter2 filter2_;

public:
    ChainedFilter(Filter1 filter1, Filter2 filter2) : filter1_(filter1), filter2_(filter2) {}

    SampleType operator()(SampleType sample) {
        return filter2_(filter1_(sample));
    }
};

// Base case: when only one filter is provided, simply return it.
template<class Filter>
auto chain_filters(Filter filter) -> Filter {
    return filter;
}

// Recursive case: chain the first filter with the rest.
template<class Filter1, class Filter2, class... Filters>
auto chain_filters(Filter1 filter1, Filter2 filter2, Filters... filters) -> ChainedFilter<Filter1, decltype(chain_filters(filter2, filters...))> {
    return ChainedFilter<Filter1, decltype(chain_filters(filter2, filters...))>(
        filter1, chain_filters(filter2, filters...)
    );
}

