#include "mymath.h"
#include <math.h>


vec3f heading(vec3f a, vec3f b) {
    return vec3f(b.x - a.x,
                b.y - a.y,
                b.z - a.z);
}

/*
double normalize_angle(double a, double norm_by) {
    while (a >= norm_by) a -= norm_by;
    while (a < 0) a += norm_by;
    return a;
}
*/

double len(vec3f a) {
    return  sqrt( pow(a.x, 2) + pow(a.y, 2) + pow(a.z, 2) );
}

/*
vec3f projection(double az, double zen, double distance) {
    double zenr=zen*DEG2RAD;
    double azr=az*DEG2RAD;
    double zens=sin(zenr);
    double zenc=cos(zenr);
    double azs=sin(azr);
    double azc=cos(azr);

    double newx = distance*azs*zens;
    double newy = distance*zenc;
    double newz = distance*azc*zens;

    //fprintf(stderr, "az=%f, zen=%f, delta=%f, %f, %f, len=%f\n", az, zen, newx, newy, newz, sqrt(newx*newx + newy*newy + newz*newz));

    return vec3f(newx, newy, newz);
}
*/

/*
vec2f rotate2(const vec2f vec, double angle) {
    //double angler = angle*DEG2RAD;
    double sa=sin(angle*DEG2RAD), ca=cos(angle*DEG2RAD);

    double x = vec.x*ca - vec.y*sa;
    double y = vec.x*sa + vec.y*ca;
    return vec2f(x, y);
}
*/


/*
void rotate3y(vec3f &vec, double angle) {
    double angler = angle*DEG2RAD;
    vec.x = vec.x*cos(angler) - vec.z*sin(angler);
    vec.z = vec.x*sin(angler) + vec.z*cos(angler);
}

void rotate3z(vec3f &vec, double angle) {
    double angler = angle*DEG2RAD;
    vec.x = vec.x*cos(angler) - vec.y*sin(angler);
    vec.y = vec.x*sin(angler) + vec.y*cos(angler);
}
*/

void translate(vec3f &vec, vec3f &trans) {
    vec.x += trans.x;
    vec.y += trans.y;
    vec.z += trans.z;
}

void mult(vec3f &vec, double m) {
    vec.x *= m;
    vec.y *= m;
    vec.z *= m;
}

double xdot(vec3f &v1, vec3f &v2) {
    return 
        v1.x*v2.x +
        v1.y*v2.y +
        v1.z*v2.z;
}

double xlength(vec3f &v) {
    return sqrt(xdot(v, v));
}

vec3f xnormal(vec3f &v1, vec3f &v2) {
    vec3f r = cross(v1, v2);
    mult(r, sqrt(xlength(r)));
    return r;
}

#define SMALL_NUM 0.0000000000001
bool line_intersect_plane(vec3f p0, vec3f p1, vec3f v0, vec3f v1, vec3f v2) {
    vec3f    u, v, n;              // triangle vectors
    vec3f    dir, w0, w;           // ray vectors
    double   r, a, b;            // params to calc ray-plane intersect

    // get triangle edge vectors and plane normal
    u = v1; xminus(u, v0);
    v = v2; xminus(v, v0);
    n = cross(u, v);               // cross product

    dir = p1; xminus(dir, p0);      // ray direction vector
    w0 = p0; xminus(w0, v0);
    a = -xdot(n,w0);
    b = xdot(n,dir);
    //printf("a=%f, b=%f\n", a, b);
    if (std::abs(b) < SMALL_NUM) {      // ray is  parallel to triangle plane
        if (a == 0) return false;   // ray lies in triangle plane
            
        else return false;         // ray disjoint from plane
    }

    // get intersect point of ray with triangle plane
    r = a / b;
    if (r < 0.0)                    // ray goes away from triangle
        return false;               // => no intersect

    vec3f I = dir;
    mult(I, r);
    translate(I, p0);             // intersect point of ray and plane
    
    // is I inside T?
    float uu, uv, vv, wu, wv, D;
    uu = xdot(u,u);
    uv = xdot(u,v);
    vv = xdot(v,v);
    w = I; xminus(w, v0);
    wu = xdot(w,u);
    wv = xdot(w,v);
    D = uv * uv - uu * vv;

    // get and test parametric coords
    float s, t;
    s = (uv * wv - vv * wu) / D;
    //printf("s == %f\n", s);
    if (s < 0.0 || s > 1.0)         // I is outside T
        return false;
    t = (uv * wu - uu * wv) / D;

    //printf("s == %f, t == %f\n", s, t);
    if (t < 0.0 || (s + t) > 1.0)  // I is outside T
        return false;

    vec3f tmp1 = v, tmp2 = u;
    mult(tmp1, t);
    mult(tmp2, s);
    translate(tmp1, tmp2);

    return true;                       // I is in T
}





