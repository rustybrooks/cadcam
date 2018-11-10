#pragma once

#define _USE_MATH_DEFINES
#include <cmath>
#include <fstream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// const used to convert degrees into radians
#ifndef TWO_PI
#define TWO_PI 2.0 * M_PI
#endif

#define RAD2DEG 180/M_PI
#define DEG2RAD M_PI/180

struct versor;
//struct vec2;
//struct vec3ff;

template <class T> struct VEC2;
template <class T> struct VEC3;

struct vec4 {
    vec4 ();
    vec4 (float x, float y, float z, float w);
    vec4 (const VEC2<float>& vv, float z, float w);
    vec4 (const VEC3<float>& vv, float w);
    float v[4];
};

template <class T>
struct VEC2 {
    VEC2() 
    //   : x(v[0])
    //    , y(v[1])
    {}

    VEC2(T x, T y) 
    //        : x(v[0])
    //    , y(v[1])
    {
        v[0] = x;
        v[1] = y;
    }

    VEC2& operator=(const VEC2& rhs) {
        v[0] = rhs.v[0];
        v[1] = rhs.v[1];
        return *this;
    }

//    T v[2];
//    T &x, &y;
    union {
        T v[2];
        struct {
            T x, y;
        };
    };
};

template <class T>
struct VEC3 {
    VEC3() 
        : x(0)
        , y(0)
        , z(0)
    {}
    
    VEC3(T x, T y, T z)
    {
        v[0] = x;
        v[1] = y;
        v[2] = z;
    }
    
    VEC3(const VEC2<T>& vv, T z)
    {
        v[0] = vv.v[0];
        v[1] = vv.v[1];
        v[2] = z;
    }
    
    VEC3(const vec4& vv) 
    {
        v[0] = vv.v[0];
        v[1] = vv.v[1];
        v[2] = vv.v[2];
    }

    const VEC3 operator+ (const VEC3& rhs) const {
        VEC3 vc;
        vc.v[0] = v[0] + rhs.v[0];
        vc.v[1] = v[1] + rhs.v[1];
        vc.v[2] = v[2] + rhs.v[2];
        return vc;
    }

    VEC3& operator+= (const VEC3& rhs) {
        v[0] += rhs.v[0];
        v[1] += rhs.v[1];
        v[2] += rhs.v[2];
        return *this; // return self
    }

    const VEC3 operator-(const VEC3& rhs) const {
        VEC3 vc;
        vc.v[0] = v[0] - rhs.v[0];
        vc.v[1] = v[1] - rhs.v[1];
        vc.v[2] = v[2] - rhs.v[2];
        return vc;
    }

    VEC3& operator-= (const VEC3& rhs) {
        v[0] -= rhs.v[0];
        v[1] -= rhs.v[1];
        v[2] -= rhs.v[2];
        return *this;
    }

    VEC3 operator+ (float rhs) {
        VEC3 vc;
        vc.v[0] = v[0] + rhs;
        vc.v[1] = v[1] + rhs;
        vc.v[2] = v[2] + rhs;
        return vc;
    }

    VEC3 operator- (float rhs) {
        VEC3 vc;
        vc.v[0] = v[0] - rhs;
        vc.v[1] = v[1] - rhs;
        vc.v[2] = v[2] - rhs;
        return vc;
    }

    const VEC3 operator/(const float rhs) const {
        VEC3 vc;
        vc.v[0] = v[0] / rhs;
        vc.v[1] = v[1] / rhs;
        vc.v[2] = v[2] / rhs;
        return vc;
    }

    VEC3& operator= (const VEC3& rhs) {
        v[0] = rhs.v[0];
        v[1] = rhs.v[1];
        v[2] = rhs.v[2];
        return *this;
    }

    template <typename TO>
    VEC3 operator* (TO rhs) const {
        VEC3 vc;
        vc.v[0] = v[0] * rhs;
        vc.v[1] = v[1] * rhs;
        vc.v[2] = v[2] * rhs;
        return vc;
    }
    
    template <typename TO>
    VEC3& operator*= (TO rhs) {
        v[0] = v[0] * rhs;
        v[1] = v[1] * rhs;
        v[2] = v[2] * rhs;
    return *this;
    }

    bool operator==(const VEC3 other) const {
        return x == other.x && y == other.y && z == other.z;
    }
	
    bool save(std::ofstream &f) {
        f.write(reinterpret_cast<char*>(v), sizeof(T)*3);
        return true;
    }

    bool load(std::ifstream &f) {
        f.read(reinterpret_cast<char*>(v), sizeof(T)*3);
        return true;
    }


    // internal data
    //T v[3];
    //T &x, &y, &z;

    union {
        T v[3];
        struct {
            T x, y, z;
        };
    };
};

typedef VEC3<float> vec3ff;
typedef VEC3<float> vec3f;
typedef VEC2<float> vec2;
typedef VEC3<int> vec3;



/* stored like this:
   0 3 6
   1 4 7
   2 5 8 */
struct mat3 {
    mat3 ();
    // note! this is entering components in ROW-major order
    mat3 (float a, float b, float c,
          float d, float e, float f,
          float g, float h, float i);
    float m[9];
};

/* stored like this:
   0 4 8  12
   1 5 9  13
   2 6 10 14
   3 7 11 15*/
struct mat4 {
    mat4 ();
    // note! this is entering components in ROW-major order
    mat4 (float a, float b, float c, float d,
          float e, float f, float g, float h,
          float i, float j, float k, float l,
          float mm, float n, float o, float p);
    vec4 operator* (const vec4& rhs);
    mat4 operator* (const mat4& rhs);
    mat4& operator= (const mat4& rhs);
    float m[16];
};

struct versor {
    versor ();
    versor operator/ (float rhs);
    versor operator* (float rhs);
    versor operator* (const versor& rhs);
    versor operator+ (const versor& rhs);

    versor mirror() {
        versor m = *this;
        m.q[0] *= -1;
        return m.normalize();
    }

    versor normalize() {
        // norm(q) = q / magnitude (q)
        // magnitude (q) = sqrt (w*w + x*x...)
        // only compute sqrt if interior sum != 1.0
        float sum = 
            q[0] * q[0] + q[1] * q[1] +
            q[2] * q[2] + q[3] * q[3];
        // NB: floats have min 6 digits of precision
        const float thresh = 0.0001f;
        if (fabs (1.0f - sum) < thresh) {
            return *this;
        }
        float mag = sqrt (sum);
        return (*this) / mag;
    }

    float q[4];
};

void print(const vec2& v);
void print(const vec3ff& v, std::string label="");
void print(const vec3& v);
void print(const vec4& v);
void print(const mat3& m);
void print(const mat4& m);

// vector functions
float length(const vec3ff& v);
float length2(const vec3ff& v);
vec3ff normalize(const vec3ff& v);
float dot(const vec3ff& a, const vec3ff& b);
vec3ff cross(const vec3ff& a, const vec3ff& b);
float get_squared_dist(vec3ff from, vec3ff to);
float direction_to_heading(vec3ff d);
vec3ff heading_to_direction(float degrees);

// matrix functions
mat3 zero_mat3 ();
mat3 identity_mat3 ();
mat4 zero_mat4 ();
mat4 identity_mat4 ();
float determinant (const mat4& mm);
mat4 inverse(const mat4& mm);
mat4 transpose (const mat4& mm);

// affine functions
mat4 translate (const mat4& m, const vec3ff& v);
mat4 rotate_x_deg (const mat4& m, float deg);
mat4 rotate_y_deg (const mat4& m, float deg);
mat4 rotate_z_deg (const mat4& m, float deg);
mat4 scale (const mat4& m, const vec3ff& v);

// quaternion functions
versor quat_from_axis_rad(float radians, float x, float y, float z);
versor quat_from_axis_deg(float degrees, float x, float y, float z);
versor quat_from_axis_rad(float radians, vec3ff v);
versor quat_from_axis_deg(float degrees, vec3ff v);

mat4 quat_to_mat4(const versor& q);
float dot(const versor& q, const versor& r);
versor slerp(const versor& q, const versor& r);

void print(const versor& q);
versor slerp(versor& q, versor& r, float t);






double normalize_angle(double a, double norm_by);
vec3ff projection(double az, double zen, double distance);
double angle_zen(vec3ff h);
double angle_az(vec3ff h);
double angle_roll(vec3ff h);



