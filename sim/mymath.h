#ifndef __mymath_h
#define __mymath_h

#include <fstream>
#include <math.h>
#include <stdlib.h>
#include <time.h>
#include <vector>

#include <boost/lexical_cast.hpp>

#include "const.h"
#include "math_funcs.h"

/*
template <class T>
struct VEC {
    VEC(T _x=0, T _y=0, T _z=0) 
        : x(_x)
        , y(_y)
        , z(_z)
    {
    }

    VEC(VEC const& foo) 
        : x(foo.x)
        , y(foo.y)
        , z(foo.z)
    {
    }

    VEC(std::vector<T> foo)
        : x(foo[0])
        , y(foo[1])
        , z(foo[2])
    {
    }

    bool save(std::ofstream &f) {
        f.write(reinterpret_cast<char*>(&x), sizeof(T));
        f.write(reinterpret_cast<char*>(&y), sizeof(T));
        f.write(reinterpret_cast<char*>(&z), sizeof(T));
        return true;
    }

    bool load(std::ifstream &f) {
        f.read(reinterpret_cast<char*>(&x), sizeof(T));
        f.read(reinterpret_cast<char*>(&y), sizeof(T));
        f.read(reinterpret_cast<char*>(&z), sizeof(T));
        return true;
    }

    bool operator==(const VEC other) const {
        return x == other.x && y == other.y && z == other.z;
    }

    VEC& operator+=(const VEC& other) {
        x += other.x;
        y += other.y;
        z += other.z;
        return *this;
    }

    const VEC operator+(const VEC &other) const {
        return VEC(x + other.x, y + other.y, z + other.z);
    }

    const VEC operator-(const VEC &other) const {
        return VEC(x - other.x, y - other.y, z - other.z);
    }

    const VEC operator*(const VEC &other) const {
        return VEC(x * other.x, y * other.y, z * other.z);
    }

    const VEC operator/(const VEC &other) const {
        return VEC(x / other.x, y / other.y, z / other.z);
    }

    const VEC operator*(const double &other) const {
        return VEC(x * other, y * other, z * other);
    }

    const VEC operator/(const double &other) const {
        return VEC(x / other, y / other, z / other);
    }

    std::string toString() {
        std::string out;
        out += "(";
        out += boost::lexical_cast<std::string>(x);
        out += ", ";
        out += boost::lexical_cast<std::string>(y);
        out += ", ";
        out += boost::lexical_cast<std::string>(z);
        out += ")";
        return out;
    }

    T x, y, z;
};
*/

//typedef vec3ff vec3f;
//typedef VEC<double> vec2f;  // yeah this is kinda dumb
//typedef VEC<int> vec3;


struct pointf {
    pointf()
        : point()
        , angles()
    {}

    pointf(pointf const &_data)
        : point(_data.point)
        , angles(_data.angles)
    {}

    pointf(vec3f _point, vec3f _angles)
        : point(_point)
        , angles(_angles)
    {}

    // assumes all 6 points will be available
    pointf(std::vector<double> _data)
        : point(_data[0], _data[1], _data[2])
        , angles(_data[3], _data[4], _data[5])
    {}

    bool operator==(const pointf other) const {
        return point == other.point && angles == other.angles;
    }

    pointf& operator+=(const pointf& other) {
        point += other.point;
        angles += other.angles;
        return *this;
    }

    const pointf operator+(const pointf &other) const {
        return pointf(point + other.point, angles + other.angles);
    }

    const pointf operator-(const pointf &other) const {
        return pointf(point - other.point, angles - other.angles);
    }

    const pointf operator*(const double other) const {
        return pointf(point * other, angles * other);
    }

    const pointf operator/(const double &other) const {
        return pointf(point / other, angles / other);
    }

    vec3ff point, angles;
};

#ifdef _WIN32

#define randinit() srand(time(NULL))
#define randreal(x) ((x) * ((double) rand() / RAND_MAX))
#define randint(x) (rand() % (x))

#else

#define randinit() srand48(time(NULL))

// returns random flat-distribution double from [0,x)
#define randreal(x) (drand48() * (x))

// returns random flat-distribution double from [0,x), intwise
#define randint(x) (lrand48() % (x))

#endif // _WIN32

// returns random flat-distribution double from [x,y)
#define rand_range(_x,_y) (_x+randreal(_y-(_x)))

vec3f heading(vec3f a, vec3f b);

double normalize_angle(double a, double norm_by=360.0);
double len(vec3f a);

//vec3f projection(double az, double zen, double distance);


void rotate3x(vec3f &vec, double const angle);
void rotate3y(vec3f &vec, double angle);
void rotate3z(vec3f &vec, double angle);
void translate(vec3f &vec, vec3f &trans);
void mult(vec3f &vec, double m);
//void xminus(vec3f &v1, vec3f &v2);
//template<class T> void xminus(T &v1, T &v2);
double xdot(vec3f &v1, vec3f &v2);
double xlength(vec3f &v);

vec3f xnormal(vec3f &v1, vec3f &v2);

template<class T>
void xdiv(T &v1, T &v2) {
    v1.x /= v2.x;
    v1.y /= v2.y;
    v1.z /= v2.z;
}
//template<class T> void xdiv(T &v1, T &v2);    

template<class T>
inline void xminus(T &v1, T &v2) {
    v1.x -= v2.x;
    v1.y -= v2.y;
    v1.z -= v2.z;
}

template<class T>
inline double xdot2(T v1[3], T v2[3]) {
    return v1[0]*v2[0] +
        v1[1]*v2[1] +
        v1[2]*v2[2];
}

template<class T>
inline void cross2(T v1[3], T v2[3], T r[3]) {
    r[0] = v1[1]*v2[2] - v1[2]*v2[1];
    r[1] = v1[2]*v2[0] - v1[0]*v2[2];
    r[2] = v1[0]*v2[1] - v1[1]*v2[0];
}

template<class T>
inline void xnormal2(T v1[3], T v2[3], T r[3]) {
    cross2(v1, v2, r);
    double d = sqrt(xdot2(r, r));
    r[0] /= d;
    r[1] /= d;
    r[2] /= d;
}

inline double angle_between(vec3f a, vec3f b) {
//    fprintf(stderr, "angle between len1=%f, len2=%f, dot=%f\n", xlength(a), xlength(b), xdot(a, b));
//    fprintf(stderr, "a = %s, b = %s\n", a.toString().c_str(), b.toString().c_str());
//    fprintf(stderr, "acos(%f) = %f\n", xdot(a, b) / (xlength(a)*xlength(b)), acos(xdot(a, b) / (xlength(a)*xlength(b))));
    double arg = xdot(a, b) / (xlength(a)*xlength(b));
//    print(a, "a");
//    print(b, "b");
//    fprintf(stderr, "arg = %f\n", arg);
        
    if (arg <= -1) {
        return 180;  // I dunno
    } else if (arg >= 1) {
        return -180; // I dunno
    } 

//    tc = cross();
//    if (xdot(vec3f(0, 0, 1), tc) < 0)

    return acos(arg) * RAD2DEG;
}


inline double _dp2(vec3f a, vec3f b, int rot_axis) {
    double sum = 0;
    for (int i=0; i<3; i++) {
        if (i == rot_axis) continue;
        sum += a.v[i]*b.v[i];
    }
    return sum;
}

inline double _len(vec3f a, int rot_axis) {
    return sqrt(_dp2(a, a, rot_axis));
}

inline vec3f _cross2(vec3f a, vec3f b, int rot_axis) {
    vec3f xa(a), xb(b);
    xa.v[rot_axis] = 0;
    xb.v[rot_axis] = 0;
    return cross(xa, xb);
}

// This is a dumb experiment
inline double _angle2(vec3f a, vec3f b, int rot_axis) {
    double angle = acos(_dp2(a, b, rot_axis) / (_len(a, rot_axis) * _len(b, rot_axis)));
//    fprintf(stderr, "l1 = %f, l2 = %f, before %f\n", _len(a, rot_axis), _len(b, rot_axis), angle);
    vec3f cr=_cross2(a, b, rot_axis);
    vec3f axis(0, 0, 0);
    axis.v[rot_axis] = 1;
    if (xdot(axis, cr) < 0) {
        angle *= -1;
    }
//    fprintf(stderr, "l1 = %f, l2 = %f, after %f\n", _len(a, rot_axis), _len(b, rot_axis), angle);

    return angle*RAD2DEG;
}



bool line_intersect_plane(vec3f p0, vec3f p1, vec3f v0, vec3f v1, vec3f v2);


#endif // __mymath_h

