#pragma once

#include <sys/time.h>

#include "mygl.h"

class SimTime {
public:
    SimTime(int _seconds=0, int _us=0) 
        : seconds(_seconds)
        , microseconds(_us)
    {}

    SimTime(double _seconds) {
        seconds = (int) _seconds;
        microseconds = (int) ((_seconds - seconds)*1e6);
    }

    SimTime operator*(int other) {
        SimTime result(*this);
        result.seconds *= other;
        result.microseconds *= other;
        return result;
    }

    SimTime operator+(SimTime &other) {
        SimTime result(*this);
        result.microseconds += other.microseconds;
        result.seconds += other.seconds;
        result.seconds += result.microseconds / 1000000;
        result.microseconds %= 1000000;
        return result;
    }

    SimTime operator-(SimTime &other) {
        return (other*-1) + *this;
    }

    bool operator>(SimTime &other) { return seconds > other.seconds && microseconds > other.microseconds; }
    bool operator>=(SimTime &other) { return seconds >= other.seconds && microseconds >= other.microseconds; }

    bool operator>(double other) { return toDouble() > other; }
    bool operator>=(double other) { return toDouble() >= other; }
    bool operator<(double other) { return toDouble() < other; }
    bool operator<=(double other) { return toDouble() <= other; }

    bool operator==(SimTime &other) {
        return ( (seconds==other.seconds) && (microseconds==other.microseconds) );
    }

    double toDouble() {
        return seconds + microseconds/1e6;
    }

    static SimTime now() {
        /* 
           struct timeval ts;
           gettimeofday(&ts, NULL);
           return GameTime(ts.tv_sec, ts.tv_usec);
        */
        
        //int time=glutGet(GLUT_ELAPSED_TIME);
        //return SimTime(time/1000, (time%1000)*1000);
        return SimTime(glfwGetTime());
    }

private:
    int seconds, microseconds;
};

SimTime now();

// 
class SimTimeCountdown {
public:
    SimTimeCountdown(double _interval) : interval(SimTime(_interval)) {
        set_timer();
    }

    SimTimeCountdown(SimTime _interval) : interval(_interval) {
        set_timer();
    }

    void set_timer() {
        wait_until = now() + interval;
    }

    bool ready(bool reset_when_ready=true) {
        if (now() >= wait_until) {
            if (reset_when_ready) wait_until = now() + interval;
            return true;
        } else {
            return false;
        }
    }

private:
    SimTime interval;
    SimTime wait_until;
};


/*
class Time : public SimTime {
public:
    Time(int _seconds=0, int _us=0) : SimTime(_seconds, _us) {}

    static Time now() {
        struct timeval ts;
        gettimeofday(&ts, NULL);
        return Time(ts.tv_sec, ts.tv_usec);
    }
};
*/    


