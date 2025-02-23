#pragma once

#include "./Common.hpp"

class DerivativeFilter
{
private:
SampleAccumType previous_;

public:
    DerivativeFilter() : previous_(0) {}

    SampleType operator()(SampleType sample)
    {
        // Prevent overflow by dividing by 2.
        SampleAccumType derivative = (sample - previous_) >> 1; 
        previous_ = sample;
        return clamped_cast(derivative);
    }
};