#pragma once

#include "./Common.hpp"
#include <cstdint>

class LowPassFilter {
private:
    // t_ is the smoothing factor in Q32 fixed-point format.
    int64_t t_;
    // 'previous_' holds the filter's state in Q32 format.
    int64_t previous_;

public:
    // The constructor takes a double in the range [0,1].
    // It converts it to Q32 fixed-point representation.
    LowPassFilter(double t) 
        : t_(static_cast<int64_t>(t * (1LL << 31))), previous_(0) {}

    SampleType operator()(SampleType sample) {
        // Convert the 16-bit sample to Q32 fixed-point.
        int64_t sample_fixed = static_cast<int64_t>(sample) << 15;
        // Update the internal state: previous_ moves fractionally toward sample_fixed.
        previous_ += ((sample_fixed - previous_) * t_) >> 31;
        // Convert back to 16-bit by shifting down.
        return clamped_cast(previous_ >> 15);
    }
};
