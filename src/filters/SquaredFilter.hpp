#pragma once

#include "./Common.hpp"

class SquaredFilter
{
public:
    SampleType operator()(SampleType sample)
    {
        return clamped_cast(SampleAccumType(sample) * SampleAccumType(sample) >> 15);
    }
};