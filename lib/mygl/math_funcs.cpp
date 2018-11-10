#include "math_funcs.h"
#include <stdio.h>
#define _USE_MATH_DEFINES
#include <math.h>

/*--------------------------------CONSTRUCTORS--------------------------------*/


vec4::vec4() {}

vec4::vec4(float x, float y, float z, float w) {
    v[0] = x;
    v[1] = y;
    v[2] = z;
    v[3] = w;
}

vec4::vec4(const VEC2<float>& vv, float z, float w) {
    v[0] = vv.v[0];
    v[1] = vv.v[1];
    v[2] = z;
    v[3] = w;
}

vec4::vec4(const VEC3<float>& vv, float w) {
    v[0] = vv.v[0];
    v[1] = vv.v[1];
    v[2] = vv.v[2];
    v[3] = w;
}

mat3::mat3() {}

/* note: entered in COLUMNS */
mat3::mat3(float a, float b, float c,
            float d, float e, float f,
            float g, float h, float i) {
    m[0] = a;
    m[1] = b;
    m[2] = c;
    m[3] = d;
    m[4] = e;
    m[5] = f;
    m[6] = g;
    m[7] = h;
    m[8] = i;
}

mat4::mat4() {}

/* note: entered in COLUMNS */
mat4::mat4(float a, float b, float c, float d,
            float e, float f, float g, float h,
            float i, float j, float k, float l,
            float mm, float n, float o, float p) {
    m[0] = a;
    m[1] = b;
    m[2] = c;
    m[3] = d;
    m[4] = e;
    m[5] = f;
    m[6] = g;
    m[7] = h;
    m[8] = i;
    m[9] = j;
    m[10] = k;
    m[11] = l;
    m[12] = mm;
    m[13] = n;
    m[14] = o;
    m[15] = p;
}

/*-----------------------------PRINT FUNCTIONS--------------------------------*/
void print(const vec2& v) {
    fprintf (stderr, "[%.2f, %.2f]\n", v.v[0], v.v[1]);
}

void print(const vec3ff& v, std::string label) {
    fprintf(stderr, "%s [%.3f, %.3f, %.3f]\n", label.c_str(), v.v[0], v.v[1], v.v[2]);
}

void print(const vec3& v) {
    fprintf(stderr, "[%d, %d, %d]\n", v.v[0], v.v[1], v.v[2]);
}

void print(const vec4& v) {
    fprintf(stderr, "[%.2f, %.2f, %.2f, %.2f]\n", v.v[0], v.v[1], v.v[2], v.v[3]);
}

void print(const mat3& m) {
    fprintf(stderr, "\n");
fprintf(stderr, "[%.2f][%.2f][%.2f]\n", m.m[0], m.m[3], m.m[6]);
fprintf(stderr, "[%.2f][%.2f][%.2f]\n", m.m[1], m.m[4], m.m[7]);
fprintf(stderr, "[%.2f][%.2f][%.2f]\n", m.m[2], m.m[5], m.m[8]);
}

void print(const mat4& m) {
    fprintf(stderr, "\n");
fprintf(stderr, "[%.2f][%.2f][%.2f][%.2f]\n", m.m[0], m.m[4], m.m[8], m.m[12]);
fprintf(stderr, "[%.2f][%.2f][%.2f][%.2f]\n", m.m[1], m.m[5], m.m[9], m.m[13]);
fprintf(stderr, "[%.2f][%.2f][%.2f][%.2f]\n", m.m[2], m.m[6], m.m[10], m.m[14]);
fprintf(stderr, "[%.2f][%.2f][%.2f][%.2f]\n", m.m[3], m.m[7], m.m[11], m.m[15]);
}

/*------------------------------VECTOR FUNCTIONS------------------------------*/
float length(const vec3ff& v) {
    return sqrt (v.v[0] * v.v[0] + v.v[1] * v.v[1] + v.v[2] * v.v[2]);
}

// squared length
float length2(const vec3ff& v) {
    return v.v[0] * v.v[0] + v.v[1] * v.v[1] + v.v[2] * v.v[2];
}

// note: proper spelling (hehe)
vec3ff normalize(const vec3ff& v) {
    vec3ff vb;
    float l = length (v);
    if (0.0f == l) {
        return vec3ff (0.0f, 0.0f, 0.0f);
    }
    vb.v[0] = v.v[0] / l;
    vb.v[1] = v.v[1] / l;
    vb.v[2] = v.v[2] / l;
    return vb;
}


float dot(const vec3ff& a, const vec3ff& b) {
    return a.v[0] * b.v[0] + a.v[1] * b.v[1] + a.v[2] * b.v[2];
}

vec3ff cross (const vec3ff& a, const vec3ff& b) {
    float x = a.v[1] * b.v[2] - a.v[2] * b.v[1];
    float y = a.v[2] * b.v[0] - a.v[0] * b.v[2];
    float z = a.v[0] * b.v[1] - a.v[1] * b.v[0];
    return vec3ff (x, y, z);
}

float get_squared_dist (vec3ff from, vec3ff to) {
    float x = (to.v[0] - from.v[0]) * (to.v[0] - from.v[0]);
    float y = (to.v[1] - from.v[1]) * (to.v[1] - from.v[1]);
    float z = (to.v[2] - from.v[2]) * (to.v[2] - from.v[2]);
    return x + y + z;
}

/* converts an un-normalized direction into a heading in degrees
   NB i suspect that the z is backwards here but i've used in in
   several places like this. d'oh! */
float direction_to_heading (vec3ff d) {
    return atan2 (-d.v[0], -d.v[2]) * RAD2DEG;
}

vec3ff heading_to_direction (float degrees) {
    float rad = degrees * DEG2RAD;
    return vec3ff (-sinf (rad), 0.0f, -cosf (rad));
}

/*-----------------------------MATRIX FUNCTIONS-------------------------------*/
mat3 zero_mat3 () {
    return mat3 (
                 0.0f, 0.0f, 0.0f,
                 0.0f, 0.0f, 0.0f,
                 0.0f, 0.0f, 0.0f
                 );
}

mat3 identity_mat3 () {
    return mat3 (
                 1.0f, 0.0f, 0.0f,
                 0.0f, 1.0f, 0.0f,
                 0.0f, 0.0f, 1.0f
                 );
}

mat4 zero_mat4() {
    return mat4(
                 0.0f, 0.0f, 0.0f, 0.0f,
                 0.0f, 0.0f, 0.0f, 0.0f,
                 0.0f, 0.0f, 0.0f, 0.0f,
                 0.0f, 0.0f, 0.0f, 0.0f
                 );
}

mat4 identity_mat4() {
    return mat4(
                 1.0f, 0.0f, 0.0f, 0.0f,
                 0.0f, 1.0f, 0.0f, 0.0f,
                 0.0f, 0.0f, 1.0f, 0.0f,
                 0.0f, 0.0f, 0.0f, 1.0f
                 );
}

/* mat4 array layout
   0  4  8 12
   1  5  9 13
   2  6 10 14
   3  7 11 15
*/

vec4 mat4::operator* (const vec4& rhs) {
    // 0x + 4y + 8z + 12w
    float x =
        m[0] * rhs.v[0] +
        m[4] * rhs.v[1] +
        m[8] * rhs.v[2] +
        m[12] * rhs.v[3];
    // 1x + 5y + 9z + 13w
    float y = m[1] * rhs.v[0] +
        m[5] * rhs.v[1] +
        m[9] * rhs.v[2] +
        m[13] * rhs.v[3];
    // 2x + 6y + 10z + 14w
    float z = m[2] * rhs.v[0] +
        m[6] * rhs.v[1] +
        m[10] * rhs.v[2] +
        m[14] * rhs.v[3];
    // 3x + 7y + 11z + 15w
    float w = m[3] * rhs.v[0] +
        m[7] * rhs.v[1] +
        m[11] * rhs.v[2] +
        m[15] * rhs.v[3];
    return vec4 (x, y, z, w);
}

mat4 mat4::operator* (const mat4& rhs) {
    mat4 r = zero_mat4();
    int r_index = 0;
    for (int col = 0; col < 4; col++) {
        for (int row = 0; row < 4; row++) {
            float sum = 0.0f;
            for (int i = 0; i < 4; i++) {
                sum += rhs.m[i + col * 4] * m[row + i * 4];
            }
            r.m[r_index] = sum;
            r_index++;
        }
    }
    return r;
}

mat4& mat4::operator=(const mat4& rhs) {
    for (int i = 0; i < 16; i++) {
        m[i] = rhs.m[i];
    }
    return *this;
}

// returns a scalar value with the determinant for a 4x4 matrix
// see http://www.euclideanspace.com/maths/algebra/matrix/functions/determinant/fourD/index.htm
float determinant(const mat4& mm) {
    return
        mm.m[12] * mm.m[9] * mm.m[6] * mm.m[3] -
        mm.m[8] * mm.m[13] * mm.m[6] * mm.m[3] -
        mm.m[12] * mm.m[5] * mm.m[10] * mm.m[3] +
        mm.m[4] * mm.m[13] * mm.m[10] * mm.m[3] +
        mm.m[8] * mm.m[5] * mm.m[14] * mm.m[3] -
        mm.m[4] * mm.m[9] * mm.m[14] * mm.m[3] -
        mm.m[12] * mm.m[9] * mm.m[2] * mm.m[7] +
        mm.m[8] * mm.m[13] * mm.m[2] * mm.m[7] +
        mm.m[12] * mm.m[1] * mm.m[10] * mm.m[7] -
        mm.m[0] * mm.m[13] * mm.m[10] * mm.m[7] -
        mm.m[8] * mm.m[1] * mm.m[14] * mm.m[7] +
        mm.m[0] * mm.m[9] * mm.m[14] * mm.m[7] +
        mm.m[12] * mm.m[5] * mm.m[2] * mm.m[11] -
        mm.m[4] * mm.m[13] * mm.m[2] * mm.m[11] -
        mm.m[12] * mm.m[1] * mm.m[6] * mm.m[11] +
        mm.m[0] * mm.m[13] * mm.m[6] * mm.m[11] +
        mm.m[4] * mm.m[1] * mm.m[14] * mm.m[11] -
        mm.m[0] * mm.m[5] * mm.m[14] * mm.m[11] -
        mm.m[8] * mm.m[5] * mm.m[2] * mm.m[15] +
        mm.m[4] * mm.m[9] * mm.m[2] * mm.m[15] +
        mm.m[8] * mm.m[1] * mm.m[6] * mm.m[15] -
        mm.m[0] * mm.m[9] * mm.m[6] * mm.m[15] -
        mm.m[4] * mm.m[1] * mm.m[10] * mm.m[15] +
        mm.m[0] * mm.m[5] * mm.m[10] * mm.m[15];
}

/* returns a 16-element array that is the inverse of a 16-element array (4x4
   matrix). see http://www.euclideanspace.com/maths/algebra/matrix/functions/inverse/fourD/index.htm */
mat4 inverse (const mat4& mm) {
    float det = determinant (mm);
    /* there is no inverse if determinant is zero (not likely unless scale is
       broken) */
    if (0.0f == det) {
        fprintf(stderr, "WARNING. matrix has no determinant. can not invert\n");
        return mm;
    }
    float inv_det = 1.0f / det;
	
    return mat4(
                 inv_det * (
                            mm.m[9] * mm.m[14] * mm.m[7] - mm.m[13] * mm.m[10] * mm.m[7] +
                            mm.m[13] * mm.m[6] * mm.m[11] - mm.m[5] * mm.m[14] * mm.m[11] -
                            mm.m[9] * mm.m[6] * mm.m[15] + mm.m[5] * mm.m[10] * mm.m[15]
                            ),
                 inv_det * (
                            mm.m[13] * mm.m[10] * mm.m[3] - mm.m[9] * mm.m[14] * mm.m[3] -
                            mm.m[13] * mm.m[2] * mm.m[11] + mm.m[1] * mm.m[14] * mm.m[11] +
                            mm.m[9] * mm.m[2] * mm.m[15] - mm.m[1] * mm.m[10] * mm.m[15]
                            ),
                 inv_det * (
                            mm.m[5] * mm.m[14] * mm.m[3] - mm.m[13] * mm.m[6] * mm.m[3] +
                            mm.m[13] * mm.m[2] * mm.m[7] - mm.m[1] * mm.m[14] * mm.m[7] -
                            mm.m[5] * mm.m[2] * mm.m[15] + mm.m[1] * mm.m[6] * mm.m[15]
                            ),
                 inv_det * (
                            mm.m[9] * mm.m[6] * mm.m[3] - mm.m[5] * mm.m[10] * mm.m[3] -
                            mm.m[9] * mm.m[2] * mm.m[7] + mm.m[1] * mm.m[10] * mm.m[7] +
                            mm.m[5] * mm.m[2] * mm.m[11] - mm.m[1] * mm.m[6] * mm.m[11]
                            ),
                 inv_det * (
                            mm.m[12] * mm.m[10] * mm.m[7] - mm.m[8] * mm.m[14] * mm.m[7] -
                            mm.m[12] * mm.m[6] * mm.m[11] + mm.m[4] * mm.m[14] * mm.m[11] +
                            mm.m[8] * mm.m[6] * mm.m[15] - mm.m[4] * mm.m[10] * mm.m[15]
                            ),
                 inv_det * (
                            mm.m[8] * mm.m[14] * mm.m[3] - mm.m[12] * mm.m[10] * mm.m[3] +
                            mm.m[12] * mm.m[2] * mm.m[11] - mm.m[0] * mm.m[14] * mm.m[11] -
                            mm.m[8] * mm.m[2] * mm.m[15] + mm.m[0] * mm.m[10] * mm.m[15]
                            ),
                 inv_det * (
                            mm.m[12] * mm.m[6] * mm.m[3] - mm.m[4] * mm.m[14] * mm.m[3] -
                            mm.m[12] * mm.m[2] * mm.m[7] + mm.m[0] * mm.m[14] * mm.m[7] +
                            mm.m[4] * mm.m[2] * mm.m[15] - mm.m[0] * mm.m[6] * mm.m[15]
                            ),
                 inv_det * (
                            mm.m[4] * mm.m[10] * mm.m[3] - mm.m[8] * mm.m[6] * mm.m[3] +
                            mm.m[8] * mm.m[2] * mm.m[7] - mm.m[0] * mm.m[10] * mm.m[7] -
                            mm.m[4] * mm.m[2] * mm.m[11] + mm.m[0] * mm.m[6] * mm.m[11]
                            ),
                 inv_det * (
                            mm.m[8] * mm.m[13] * mm.m[7] - mm.m[12] * mm.m[9] * mm.m[7] +
                            mm.m[12] * mm.m[5] * mm.m[11] - mm.m[4] * mm.m[13] * mm.m[11] -
                            mm.m[8] * mm.m[5] * mm.m[15] + mm.m[4] * mm.m[9] * mm.m[15]
                            ),
                 inv_det * (
                            mm.m[12] * mm.m[9] * mm.m[3] - mm.m[8] * mm.m[13] * mm.m[3] -
                            mm.m[12] * mm.m[1] * mm.m[11] + mm.m[0] * mm.m[13] * mm.m[11] +
                            mm.m[8] * mm.m[1] * mm.m[15] - mm.m[0] * mm.m[9] * mm.m[15]
                            ),
                 inv_det * (
                            mm.m[4] * mm.m[13] * mm.m[3] - mm.m[12] * mm.m[5] * mm.m[3] +
                            mm.m[12] * mm.m[1] * mm.m[7] - mm.m[0] * mm.m[13] * mm.m[7] -
                            mm.m[4] * mm.m[1] * mm.m[15] + mm.m[0] * mm.m[5] * mm.m[15]
                            ),
                 inv_det * (
                            mm.m[8] * mm.m[5] * mm.m[3] - mm.m[4] * mm.m[9] * mm.m[3] -
                            mm.m[8] * mm.m[1] * mm.m[7] + mm.m[0] * mm.m[9] * mm.m[7] +
                            mm.m[4] * mm.m[1] * mm.m[11] - mm.m[0] * mm.m[5] * mm.m[11]
                            ),
                 inv_det * (
                            mm.m[12] * mm.m[9] * mm.m[6] - mm.m[8] * mm.m[13] * mm.m[6] -
                            mm.m[12] * mm.m[5] * mm.m[10] + mm.m[4] * mm.m[13] * mm.m[10] +
                            mm.m[8] * mm.m[5] * mm.m[14] - mm.m[4] * mm.m[9] * mm.m[14]
                            ),
                 inv_det * (
                            mm.m[8] * mm.m[13] * mm.m[2] - mm.m[12] * mm.m[9] * mm.m[2] +
                            mm.m[12] * mm.m[1] * mm.m[10] - mm.m[0] * mm.m[13] * mm.m[10] -
                            mm.m[8] * mm.m[1] * mm.m[14] + mm.m[0] * mm.m[9] * mm.m[14]
                            ),
                 inv_det * (
                            mm.m[12] * mm.m[5] * mm.m[2] - mm.m[4] * mm.m[13] * mm.m[2] -
                            mm.m[12] * mm.m[1] * mm.m[6] + mm.m[0] * mm.m[13] * mm.m[6] +
                            mm.m[4] * mm.m[1] * mm.m[14] - mm.m[0] * mm.m[5] * mm.m[14]
                            ),
                 inv_det * (
                            mm.m[4] * mm.m[9] * mm.m[2] - mm.m[8] * mm.m[5] * mm.m[2] +
                            mm.m[8] * mm.m[1] * mm.m[6] - mm.m[0] * mm.m[9] * mm.m[6] -
                            mm.m[4] * mm.m[1] * mm.m[10] + mm.m[0] * mm.m[5] * mm.m[10]
                            )
                 );
}

// returns a 16-element array flipped on the main diagonal
mat4 transpose (const mat4& mm) {
    return mat4(
                 mm.m[0], mm.m[4], mm.m[8], mm.m[12],
                 mm.m[1], mm.m[5], mm.m[9], mm.m[13],
                 mm.m[2], mm.m[6], mm.m[10], mm.m[14],
                 mm.m[3], mm.m[7], mm.m[11], mm.m[15]
                 );
}

/*--------------------------AFFINE MATRIX FUNCTIONS---------------------------*/
// translate a 4d matrix with xyz array
mat4 translate (const mat4& m, const vec3ff& v) {
    mat4 m_t = identity_mat4();
    m_t.m[12] = v.v[0];
    m_t.m[13] = v.v[1];
    m_t.m[14] = v.v[2];
    return m_t * m;
}

// rotate around x axis by an angle in degrees
mat4 rotate_x_deg (const mat4& m, float deg) {
    // convert to radians
    float rad = deg * DEG2RAD;
    mat4 m_r = identity_mat4();
    m_r.m[5] = cos (rad);
    m_r.m[9] = -sin (rad);
    m_r.m[6] = sin (rad);
    m_r.m[10] = cos (rad);
    return m_r * m;
}

// rotate around y axis by an angle in degrees
mat4 rotate_y_deg (const mat4& m, float deg) {
    // convert to radians
    float rad = deg * DEG2RAD;
    mat4 m_r = identity_mat4();
    m_r.m[0] = cos (rad);
    m_r.m[8] = sin (rad);
    m_r.m[2] = -sin (rad);
    m_r.m[10] = cos (rad);
    return m_r * m;
}

// rotate around z axis by an angle in degrees
mat4 rotate_z_deg (const mat4& m, float deg) {
    // convert to radians
    float rad = deg * DEG2RAD;
    mat4 m_r = identity_mat4();
    m_r.m[0] = cos (rad);
    m_r.m[4] = -sin (rad);
    m_r.m[1] = sin (rad);
    m_r.m[5] = cos (rad);
    return m_r * m;
}

// scale a matrix by [x, y, z]
mat4 scale (const mat4& m, const vec3ff& v) {
    mat4 a = identity_mat4();
    a.m[0] = v.v[0];
    a.m[5] = v.v[1];
    a.m[10] = v.v[2];
    return a * m;
}

/*-----------------------VIRTUAL CAMERA MATRIX FUNCTIONS----------------------*/
// returns a view matrix using the opengl lookAt style. COLUMN ORDER.


/*----------------------------HAMILTON IN DA HOUSE!---------------------------*/
versor::versor() { 
    q[0] = 1;
    q[1] = 0;
    q[2] = 0;
    q[3] = 0;
}

versor versor::operator/ (float rhs) {
    versor result;
    result.q[0] = q[0] / rhs;
    result.q[1] = q[1] / rhs;
    result.q[2] = q[2] / rhs;
    result.q[3] = q[3] / rhs;
    return result;
}

versor versor::operator* (float rhs) {
    versor result;
    result.q[0] = q[0] * rhs;
    result.q[1] = q[1] * rhs;
    result.q[2] = q[2] * rhs;
    result.q[3] = q[3] * rhs;
    return result;
}

void print(const versor& q) {
    fprintf(stderr, "[%.2f ,%.2f, %.2f, %.2f]\n", q.q[0], q.q[1], q.q[2], q.q[3]);
}

versor versor::operator* (const versor& rhs) {
    versor result;
    result.q[0] = rhs.q[0] * q[0] - rhs.q[1] * q[1] -
        rhs.q[2] * q[2] - rhs.q[3] * q[3];
    result.q[1] = rhs.q[0] * q[1] + rhs.q[1] * q[0] -
        rhs.q[2] * q[3] + rhs.q[3] * q[2];
    result.q[2] = rhs.q[0] * q[2] + rhs.q[1] * q[3] +
        rhs.q[2] * q[0] - rhs.q[3] * q[1];
    result.q[3] = rhs.q[0] * q[3] - rhs.q[1] * q[2] +
        rhs.q[2] * q[1] + rhs.q[3] * q[0];
    // re-normalize in case of mangling
    return result.normalize();
}

versor versor::operator+ (const versor& rhs) {
    versor result;
    result.q[0] = rhs.q[0] + q[0];
    result.q[1] = rhs.q[1] + q[1];
    result.q[2] = rhs.q[2] + q[2];
    result.q[3] = rhs.q[3] + q[3];
    // re-normalize in case of mangling
    return result.normalize();
}

versor quat_from_axis_rad (float radians, float x, float y, float z) {
    versor result;
    result.q[0] = cos (radians / 2.0);
    result.q[1] = sin (radians / 2.0) * x;
    result.q[2] = sin (radians / 2.0) * y;
    result.q[3] = sin (radians / 2.0) * z;
    return result;
}

versor quat_from_axis_deg (float degrees, float x, float y, float z) {
    return quat_from_axis_rad (DEG2RAD * degrees, x, y, z);
}

versor quat_from_axis_rad (float radians, vec3ff v) {
    versor result;
    result.q[0] = cos (radians / 2.0);
    result.q[1] = sin (radians / 2.0) * v.v[0];
    result.q[2] = sin (radians / 2.0) * v.v[1];
    result.q[3] = sin (radians / 2.0) * v.v[2];
    return result;
}

versor quat_from_axis_deg (float degrees, vec3ff v) {
    return quat_from_axis_rad (DEG2RAD * degrees, v);
}


mat4 quat_to_mat4(const versor& q) {
    float w = q.q[0];
    float x = q.q[1];
    float y = q.q[2];
    float z = q.q[3];
    return mat4(
                 1.0f - 2.0f * y * y - 2.0f * z * z,
                 2.0f * x * y + 2.0f * w * z,
                 2.0f * x * z - 2.0f * w * y,
                 0.0f,
                 2.0f * x * y - 2.0f * w * z,
                 1.0f - 2.0f * x * x - 2.0f * z * z,
                 2.0f * y * z + 2.0f * w * x,
                 0.0f,
                 2.0f * x * z + 2.0f * w * y,
                 2.0f * y * z - 2.0f * w * x,
                 1.0f - 2.0f * x * x - 2.0f * y * y,
                 0.0f,
                 0.0f,
                 0.0f,
                 0.0f,
                 1.0f
                 );
}

float dot (const versor& q, const versor& r) {
    return q.q[0] * r.q[0] + q.q[1] * r.q[1] + q.q[2] * r.q[2] + q.q[3] * r.q[3];
}

versor slerp (versor& q, versor& r, float t) {
    // angle between q0-q1
    float cos_half_theta = dot (q, r);
    // as found here http://stackoverflow.com/questions/2886606/flipping-issue-when-interpolating-rotations-using-quaternions
    // if dot product is negative then one quaternion should be negated, to make
    // it take the short way around, rather than the long way
    // yeah! and furthermore Susan, I had to recalculate the d.p. after this
    if (cos_half_theta < 0.0f) {
        for (int i = 0; i < 4; i++) {
            q.q[i] *= -1.0f;
        }
        cos_half_theta = dot (q, r);
    }
    // if qa=qb or qa=-qb then theta = 0 and we can return qa
    if (fabs (cos_half_theta) >= 1.0f) {
        return q;
    }
    // Calculate temporary values
    float sin_half_theta = sqrt (1.0f - cos_half_theta * cos_half_theta);
    // if theta = 180 degrees then result is not fully defined
    // we could rotate around any axis normal to qa or qb
    versor result;
    if (fabs (sin_half_theta) < 0.001f) {
        for (int i = 0; i < 4; i++) {
            result.q[i] = (1.0f - t) * q.q[i] + t * r.q[i];
        }
        return result;
    }
    float half_theta = acos (cos_half_theta);
    float a = sin ((1.0f - t) * half_theta) / sin_half_theta;
    float b = sin (t * half_theta) / sin_half_theta;
    for (int i = 0; i < 4; i++) {
        result.q[i] = q.q[i] * a + r.q[i] * b;
    }
    return result;
}




vec3ff projection(double az, double zen, double distance) {
    double zenr=zen*DEG2RAD;
    double azr=az*DEG2RAD;
    //fprintf(stderr,  "zen=%f, zenr=%f, az=%f, azr=%f\n", zen, zenr, az, azr);
    double zens=sin(zenr);
    double zenc=cos(zenr);
    double azs=sin(azr);
    double azc=cos(azr);
    //fprintf(stderr, "zens=%f, zenc=%f, azs=%f, azc=%f\n", zens, zenc, azs, azc);

    double newx = distance*azs*zens;
    double newy = distance*zenc;
    double newz = distance*azc*zens;

    //fprintf(stderr, "az=%f, zen=%f, delta=%f, %f, %f, len=%f, DTR=%f, M_PI=%f\n", az, zen, newx, newy, newz, sqrt(newx*newx + newy*newy + newz*newz), DEG2RAD, M_PI);

    return vec3ff(newx, newy, newz);
}


double normalize_angle(double a, double norm_by) {
    while (a >= norm_by) a -= norm_by;
    while (a < 0) a += norm_by;
    return a;
}

double angle_zen(vec3ff h) {
    double r = length(h);

    return normalize_angle(acos(h.v[1] / r) * RAD2DEG, 180.0);
}

double angle_az(vec3ff h) {
    return normalize_angle(atan2(h.v[0], h.v[2]) * RAD2DEG, 360.0);
}

// def not right.  No idea.
double angle_roll(vec3ff h) {
    double r = length(h);
    return normalize_angle(asin(h.v[2] / r) * RAD2DEG, 360.0);
}


vec2 rotate2(const vec2 vec, double angle) {
    //double angler = angle*DEG2RAD;
    double sa=sin(angle*DEG2RAD), ca=cos(angle*DEG2RAD);

    double x = vec.v[0]*ca - vec.v[1]*sa;
    double y = vec.v[0]*sa + vec.v[1]*ca;
    return vec2(x, y);
}

void rotate3x(vec3ff &vec, double angle) {
    vec2 tmp = rotate2(vec2(vec.y, vec.z), angle);
    vec.y = tmp.x;
    vec.z = tmp.y;
}

void rotate3y(vec3ff &vec, double angle) {
    vec2 tmp = rotate2(vec2(vec.x, vec.z), angle);
    vec.x = tmp.x;
    vec.z = tmp.y ;
}

void rotate3z(vec3ff &vec, double angle) {
    vec2 tmp = rotate2(vec2(vec.x, vec.y), angle);
    vec.x = tmp.x;
    vec.y = tmp.y;
}

