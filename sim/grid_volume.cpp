#include "grid_volume.h"

vec3ff normTable[256][5];
vec3ff bigintVerts[12];

void linear_interp2(vec3 v1, vec3 v2, vec3ff &res) {
    res.x = (v1.x + v2.x)/2.0;
    res.y = (v1.y + v2.y)/2.0;
    res.z = (v1.z + v2.z)/2.0;
}

void generate_normals() {
    vec3 verts[8];
    //vec3ff intVerts[12];

    verts[0] = vec3(0, 0, 0);
    verts[1] = vec3(1, 0, 0);
    verts[2] = vec3(1, 0, 1);
    verts[3] = vec3(0, 0, 1);
    verts[4] = vec3(0, 1, 0);
    verts[5] = vec3(1, 1, 0);
    verts[6] = vec3(1, 1, 1);
    verts[7] = vec3(0, 1, 1);

    linear_interp2(verts[0], verts[1], bigintVerts[0]);
    linear_interp2(verts[1], verts[2], bigintVerts[1]);
    linear_interp2(verts[2], verts[3], bigintVerts[2]);
    linear_interp2(verts[3], verts[0], bigintVerts[3]);
    linear_interp2(verts[4], verts[5], bigintVerts[4]);
    linear_interp2(verts[5], verts[6], bigintVerts[5]);
    linear_interp2(verts[6], verts[7], bigintVerts[6]);
    linear_interp2(verts[7], verts[4], bigintVerts[7]);
    linear_interp2(verts[0], verts[4], bigintVerts[8]);
    linear_interp2(verts[1], verts[5], bigintVerts[9]);
    linear_interp2(verts[2], verts[6], bigintVerts[10]);
    linear_interp2(verts[3], verts[7], bigintVerts[11]);

    vec3ff tri[3];
    vec3ff norm;
    vec3ff off1, off2;
    int cubeIndex;

    for (cubeIndex = 0; cubeIndex < 256; cubeIndex++) {
        int foo = 0;
        for (int n=0; triTable[cubeIndex][n] != -1; n+=3) {
            tri[0] = bigintVerts[triTable[cubeIndex][n]];
            tri[1] = bigintVerts[triTable[cubeIndex][n+1]];
            tri[2] = bigintVerts[triTable[cubeIndex][n+2]];
            off1 = tri[1] - tri[0];
            off2 = tri[2] - tri[0];
            
            normTable[cubeIndex][foo++] = normalize(cross(off1, off2));
        }
    }
}

