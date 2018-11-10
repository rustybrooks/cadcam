#pragma once

#include "math.h"

#include <algorithm>    
#include <cstdarg>
#include <fstream>

#include <boost/foreach.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/unordered_map.hpp>
#include <boost/thread/mutex.hpp>

#include "bit.h"
#include "mymath.h"
#include "mygl.h"
#include "marching_cubes_table.h"
#include "sim_time.h"
#include "world.h"

struct ihash2 : std::unary_function<vec3, std::size_t> {
    std::size_t operator()(vec3 const& e) const {
        std::size_t seed = 0;
        boost::hash_combine( seed, e.x );
        boost::hash_combine( seed, e.y );
        boost::hash_combine( seed, e.z );
        return seed;
    }
};

extern vec3ff normTable[256][5];
extern vec3ff bigintVerts[12];

void generate_normals();


struct SubGridVolume : public World::Drawable {

    SubGridVolume(vec3 _index=vec3(0,0,0), vec3ff _start=vec3ff(0, 0, 0), vec3 _gridsize=vec3(1,1,1))
        : World::Drawable()
        , index(_index)
        , dirty(true)
        , vbo_dirty(false)
        , calculating(false)
        , first(true)
        , framebuffer_first(true)
    {
        double x, y, z;
        x = _start.x;
        y = _start.y;
        z = _start.z;
        
        vec3 off(_gridsize);
        bbox.push_back(vec3ff(x,        y,        z));
        bbox.push_back(vec3ff(x+off.x,  y,        z));
        bbox.push_back(vec3ff(x+off.x,  y,        z+off.z));
        bbox.push_back(vec3ff(x,        y,        z+off.z));
        
        bbox.push_back(vec3ff(x,        y+off.y,  z));
        bbox.push_back(vec3ff(x+off.x,  y+off.y,  z));
        bbox.push_back(vec3ff(x+off.x,  y+off.y,  z+off.z));
        bbox.push_back(vec3ff(x,        y+off.y,  z+off.z));

        _vertices.resize(2 << 14);
        _vertices2.resize(_vertices.size());
        _normals.resize(_vertices.size());
        _normals2.resize(_vertices.size());

        num_vertices = 0;
        num_vertices2 = 0;
        
    }

    void log(const char* fmt...) {
        va_list args;
        fprintf(stderr, "subgrid (%d, %d, %d): ", index.x, index.y, index.z);
        va_start(args, fmt);
        vfprintf(stderr, fmt, args);
        va_end(args);
    }

    

    void render() {
//        boost::mutex::scoped_lock lock(gl_mutex);

        //if (vbo_dirty && !calculating) {
        //    setup_vbo();
        //}

        glBindVertexArray(vao(true));
        _shader->use();
        render_location();

        if (framebuffer_first) {
            glDrawArrays(GL_TRIANGLES, 0, num_vertices);
        } else {
            glDrawArrays(GL_TRIANGLES, 0, num_vertices2);
        }
    }

    void setup_vbo() {
        if (!vbo_dirty) return;

        glBindVertexArray(vao(false));

        vbo_num = 0;
        if (_shader->requires_positions()) {
            if (first) glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            if (!framebuffer_first) {
                if (_vertices.size()) 
                    glBufferData(GL_ARRAY_BUFFER, _vertices.size()*sizeof(GLfloat)*3, _vertices.data(), GL_STATIC_DRAW);
            } else {
                if (_vertices2.size()) 
                    glBufferData(GL_ARRAY_BUFFER, _vertices2.size()*sizeof(GLfloat)*3, _vertices2.data(), GL_STATIC_DRAW);
            }

            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        if (_shader->requires_colors()) {
            if (first) glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            if (!framebuffer_first) {
                if (_colors.size()) 
                    glBufferData(GL_ARRAY_BUFFER, _colors.size()*sizeof(GLfloat)*3, _colors.data(), GL_STATIC_DRAW);
            } else { 
                if (_colors2.size()) 
                    glBufferData(GL_ARRAY_BUFFER, _colors2.size()*sizeof(GLfloat)*3, _colors2.data(), GL_STATIC_DRAW);
            }
            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }

        if (_shader->requires_normals()) {
            if (first) glGenBuffers(1, &vbo[vbo_num]);
            glBindBuffer(GL_ARRAY_BUFFER, vbo[vbo_num]);
            if (!framebuffer_first) {
                if (_normals.size()) 
                    glBufferData(GL_ARRAY_BUFFER, _normals.size()*sizeof(GLfloat)*3, _normals.data(), GL_STATIC_DRAW);
            } else {
                if (_normals2.size()) 
                    glBufferData(GL_ARRAY_BUFFER, _normals2.size()*sizeof(GLfloat)*3, _normals2.data(), GL_STATIC_DRAW);
            }
            glVertexAttribPointer(vbo_num, 3, GL_FLOAT, GL_FALSE, 0, NULL);
            glEnableVertexAttribArray(vbo_num);
            vbo_num++;
        }        
        first = false;

        swap_vao();
        framebuffer_first = framebuffer_first ? 0 : 1;
        vbo_dirty = false;
    }

    vec3 index;
    vec3ff start;
    vector<vec3ff> bbox;
    bool dirty, vbo_dirty, calculating, first;

    vector<vec3ff> _vertices, _normals, _colors;
    vector<vec3ff> _vertices2, _normals2, _colors2;
    int num_vertices, num_vertices2;
    bool framebuffer_first;
    boost::mutex gl_mutex;
};

typedef boost::unordered_map<vec3,SubGridVolume,ihash2> SubGridVolumeMap;
//typedef boost::unordered_map<vec3ff,vector<SubGridVolume*>, ihash2f> PointToGridMap;

//typedef std::pair<vec3,SubGridVolume> SubGridVolumePair; std::pair<vec3ff,vector<SubGridVolume*> > SubGridPointMapPair;


/*******************************************************************************************************************/

#define SUBSTEP 200
class GridVolume {

public:
    // This should really only be used if you're going to initialize the class data from somewhere else, like a file
    GridVolume()
        : rotx(0)
        , dirty(true)
        , substep(SUBSTEP, SUBSTEP, SUBSTEP)
    {
        fprintf(stderr, "This is dirty and you shouldn't see it much\n");
    }

    GridVolume(vec3ff _start, vec3ff _bounds, double _res)
        : resolution(_res)
        , rotx(0)
        , start(_start)
        , bounds(_bounds)
        , dirty(true)
        , calculating(false)
        , needs_refresh(false)
        , substep(SUBSTEP, SUBSTEP, SUBSTEP)
    {
        init();
    }

    ~GridVolume() {
        // FIXME
        /*
        for (SubGridVolumeMap::iterator it=subgrid.begin(); it!=subgrid.end(); it++) {
            delete it->second;
        }
        */
    }

    void init() {
        maxstep = vec3(
            bounds.x / resolution,
            bounds.y / resolution,
            bounds.z / resolution
        );
        
        maxyz = (maxstep.y+2)*(maxstep.z+2);
        int size = (maxstep.x+2)*(maxstep.y+2)*(maxstep.z+2);
        deleted.assign(size, true);
        entrenched.assign(size, false);
        
        int offset;
        for (int i=1; i<maxstep.x-1; i++) {
            for (int j=1; j<maxstep.y-1; j++) {
                for (int k=1; k<maxstep.z-1; k++) {
                    offset = get_offset(i, j, k);
                    entrenched[offset] = true;
                }
            }
        }

        for (int i=0; i<maxstep.x; i++) {
            for (int j=0; j<maxstep.y; j++) {
                for (int k=0; k<maxstep.z; k++) {
                    offset = get_offset(i, j, k);
                    deleted[offset] = false;
                }
            }
        }


        if (maxstep.x < substep.x) substep.x = maxstep.x+1;
        if (maxstep.y < substep.y) substep.y = maxstep.y+1;
        if (maxstep.z < substep.z) substep.z = maxstep.z+1;

//        fprintf(stderr, "Step sizes are %d, %d, %d, total items = %f mm\n", maxstep.x, maxstep.y, maxstep.z, (1.0*maxstep.x*maxstep.y*maxstep.z)/1e6);

        int lasti = (int(maxstep.x / substep.x)+1)*substep.x;
        int lastj = (int(maxstep.y / substep.y)+1)*substep.y;
        int lastk = (int(maxstep.z / substep.z)+1)*substep.z;

        vec3 ind;
        for (int i=0; i<lasti; i+=substep.x) {
            for (int j=0; j<lastj; j+=substep.y) {
                for (int k=0; k<lastk; k+=substep.z) {
                    ind = vec3(i, j, k);
                    //fprintf(stderr, "Creating subgrid %d, %d, %d\n", i, j, k);
                    subgrid.emplace(
                        std::piecewise_construct,
                        std::forward_as_tuple(i, j, k),
                        std::forward_as_tuple(ind, coords(ind), substep*resolution)
                    );
                }
            }
        }

//        fprintf(stderr, "Created %lu subgrids\n", subgrid.size());

//        SimTime start(SimTime::now());
        generate_normals();
//        printf("generate_normals took %0.4f\n", (SimTime::now() - start).toDouble());
    }

    void render(bool update_marching=false) {
        if (update_marching) {
            marching_cubes();
        }

        if (needs_refresh && !calculating) {
//            SimTime start(SimTime::now());
            boost::mutex::scoped_lock lock(gl_mutex);
            for (SubGridVolumeMap::iterator it=subgrid.begin(); it!=subgrid.end(); it++) {
                it->second.setup_vbo();
            }
            needs_refresh = false;
//            printf("Refresh took (%0.4f)\n", (SimTime::now() - start).toDouble());
        }

        for (SubGridVolumeMap::iterator it=subgrid.begin(); it!=subgrid.end(); it++) {
            it->second.render();
        }
    }

    void set_shader(Camera &c, ShaderEnum shader_type, std::string base=std::string()) {
        for (SubGridVolumeMap::iterator it=subgrid.begin(); it!=subgrid.end(); it++) {
            it->second.set_shader(c, shader_type, base);
        }
    }

    // probably this isn't required since the shader owns the value??
    void setUniformVector3f(char *name, vec3ff &value) {
        for (SubGridVolumeMap::iterator it=subgrid.begin(); it!=subgrid.end(); it++) {
            it->second._shader->use();
            it->second.setUniformVector3f(name, value);
        }
    }

    bool save(std::string filename) {
        ofstream f(filename, std::ios::out | std::ios::binary);
        return save(f);
    }

    bool save(std::ofstream &f) {
        f.write(reinterpret_cast<char*>(&resolution), sizeof(resolution));
        start.save(f);
        bounds.save(f);
        size_t size = deleted.size();
        f.write(reinterpret_cast<char *>(&size), sizeof(size));
        int bits=0;
        uint8_t byte = 0;
        size_t delcount = 0;
        for (size_t i=0; i<size; i++) {
            delcount += deleted[i] ? 1 : 0;
            byte |= (uint8_t) (deleted[i] ? pow(2, 7-bits) : 0);
            bits++;
            if (bits == 8) {
                f.write(reinterpret_cast<char*>(&byte), sizeof(uint8_t));
                bits = 0; byte = 0;
            }
        }
        if (bits != 0) {
            f.write(reinterpret_cast<char*>(&byte), sizeof(uint8_t));
        }

        fprintf(stderr, "Deleted %lu / %lu\n", delcount, size);
        return true;
    }

    bool load(std::string filename, bool flipx=false) {
        fprintf(stderr, "Loading grid data from %s\n", filename.c_str());
        ifstream f(filename, std::ios::in | std::ios::binary);
        f.exceptions(std::ios::failbit | std::ios::badbit);
        return load(f, flipx);
    }

    bool load(ifstream &f, bool flipx=false) {
        size_t size, bmax;

        f.read(reinterpret_cast<char*>(&resolution), sizeof(resolution));
        start.load(f);
        bounds.load(f);
        init();

        f.read(reinterpret_cast<char*>(&size), sizeof(size));
        bmax = static_cast<size_t>(ceil(size / 8.0));
        uint8_t byte;
        size_t counter = 0, delcount = 0;
        for (size_t b=0; b<bmax; b++) {
            f.read(reinterpret_cast<char*>(&byte), sizeof(uint8_t));
            for (int bit=0; bit<8; bit++) {
                deleted[counter] = (byte & static_cast<uint8_t>(pow(2, 7-bit))) >> (7-bit);
                if (deleted[counter]) delcount++;
                counter++;
                if (counter == size) break;
                if (counter % 2000000 == 0) {
                    fprintf(stderr, "Counter = %lu / %lu\n", counter, size);
                }
            }
        }

        vector<bool> new_deleted(deleted.size(), true);
        if (flipx) {
            fprintf(stderr, "Flipping the x %d, %d, %d\n", maxstep.x, maxstep.y, maxstep.z);
            int offset1, offset2;
            for (int i=0; i<maxstep.x; i++) {
                for (int j=0; j<maxstep.y; j++) {
                    for (int k=0; k<maxstep.z; k++) {
                        offset1 = get_offset(i, j, k);
                        offset2 = get_offset(i, maxstep.y-j-1, k);
                        new_deleted[offset1] = deleted[offset2];
                    }
                }
            }
            std::copy(new_deleted.begin(), new_deleted.end(), deleted.begin());
        }

        fprintf(stderr, "Length of deleted %lu (%lu), delcount = %lu\n", deleted.size(), size, delcount);
        return true;
    }

    void marching_cubes_subgrid(SubGridVolume& subgrid) {
//        boost::mutex::scoped_lock lock(subgrid.gl_mutex);
        subgrid.calculating = true;

        //fprintf(stderr, "marching cubes subgrid (%d, %d, %d)\n", subgrid.index.x, subgrid.index.y, subgrid.index.z);

        vector<vec3ff> *these_vertices;
        vector<vec3ff> *these_normals;
        if (subgrid.framebuffer_first) {
            these_vertices = &subgrid._vertices2;
            these_normals = &subgrid._normals2;
        } else {
            these_vertices = &subgrid._vertices;
            these_normals = &subgrid._normals;
        }

        size_t num = 0;

        const int istart = subgrid.index.x - 1;
        const int jstart = subgrid.index.y - 1;
        const int kstart = subgrid.index.z - 1;

        const int iend = std::min(maxstep.x+1, istart + substep.x + 1);
        const int jend = std::min(maxstep.y+1, jstart + substep.y + 1);
        const int kend = std::min(maxstep.z+1, kstart + substep.z + 1);

        vec3 verts[8];

        int cubeIndex;
        int i, j, k;
        vec3ff base;

        for (i=istart; i<iend; i++) {
            for (j=jstart; j<jend; j++) {
                for (k=kstart; k<kend; k++) {
                    verts[0] = vec3(i  , j  , k  );
//                    if (is_entrenched(verts[0])) {
//                        continue;
//                    } 
                    verts[1] = vec3(i+1, j  , k  );
                    verts[2] = vec3(i+1, j  , k+1);
                    verts[3] = vec3(i  , j  , k+1);
                    verts[4] = vec3(i  , j+1, k  );
                    verts[5] = vec3(i+1, j+1, k  );
                    verts[6] = vec3(i+1, j+1, k+1);
                    verts[7] = vec3(i  , j+1, k+1);

                    cubeIndex = 0;
                    base = vec3ff(i, j, k);
                    
                    for (int n=0; n < 8; n++)
                        if (!is_deleted_fast(verts[n])) cubeIndex |= (1 << n);
                    
                    if (!edgeTable[cubeIndex]) continue;

                    for (int n=0; triTable[cubeIndex][n] != -1; n+=1) {
                        if (num >= these_vertices->size()) {
                            these_vertices->resize((size_t) these_vertices->size()*2);
                            these_normals->resize((size_t) these_vertices->size());
                        }
                        
                        (*these_vertices)[num] = coords(bigintVerts[triTable[cubeIndex][n]] + base);
                        (*these_normals)[num] = normTable[cubeIndex][n/3];
                        num++;
                    }
                }
            }
        }

        if (subgrid.framebuffer_first) {
            subgrid.num_vertices2 = num;
        } else {
            subgrid.num_vertices = num;
        }

        subgrid.vbo_dirty = true;
        subgrid.calculating = false;
        subgrid.dirty = false;
    }

    void marching_cubes() {
        if (!dirty) return;

        boost::mutex::scoped_lock lock(gl_mutex);
        calculating = true;

//        SimTime start(SimTime::now());
        int did =0;
        for (SubGridVolumeMap::iterator it=subgrid.begin(); it!=subgrid.end(); it++) {
            if (!it->second.dirty) continue;
            did++;
            marching_cubes_subgrid(it->second);
        }
//        printf("Calculated MC for %d / %lu (%0.4f)\n", did, subgrid.size(), (SimTime::now() - start).toDouble());

        calculating = false;
        needs_refresh = true;

        dirty = false;
    }

    void remove_intersection(Bit const &bit) {

        vec3ff bb_start=bit.get_start(true), bb_end=bit.get_start(true);
        bit.bounding_box(bb_start, bb_end);
//        print(bb_start, "start");
//        print(bb_end, "end");
        vec3 bb_start_i = index(bb_start);
        vec3 bb_end_i = index(bb_end);

        // no point going out of bounds of our grid
        if (bb_start_i.x < 1) bb_start_i.x = 1;
        if (bb_start_i.y < 1) bb_start_i.y = 1;
        if (bb_start_i.z < 1) bb_start_i.z = 1;
        if (bb_start_i.x > maxstep.x-1) bb_start_i.x = maxstep.x-1;
        if (bb_start_i.y > maxstep.y-1) bb_start_i.y = maxstep.y-1;
        if (bb_start_i.z > maxstep.z-1) bb_start_i.z = maxstep.z-1;
        if (bb_end_i.x < 1) bb_end_i.x = 1;
        if (bb_end_i.y < 1) bb_end_i.y = 1;
        if (bb_end_i.z < 1) bb_end_i.z = 1;
        if (bb_end_i.x > maxstep.x-1) bb_end_i.x = maxstep.x-1;
        if (bb_end_i.y > maxstep.y-1) bb_end_i.y = maxstep.y-1;
        if (bb_end_i.z > maxstep.z-1) bb_end_i.z = maxstep.z-1;

        // tmp test - prob something to this, bounding box is fucked
        /*
        bb_start_i.x = 1;
        bb_start_i.y = 1;
        bb_start_i.z = 1;
        bb_end_i.x = maxstep.x-1;
        bb_end_i.y = maxstep.y-1;
        bb_end_i.z = maxstep.z-1;
        */

        int lasti, lastj, lastk;
        lasti = bb_end_i.x+1;
        lastj = bb_end_i.y+1;
        lastk = bb_end_i.z+1;

        vec3ff xxx;
        for (int i=bb_start_i.x-1; i<lasti; i++) {
            for (int j=bb_start_i.y-1; j<lastj; j++) {
                for (int k=bb_start_i.z - 1; k<lastk; k++) {
                    vec3 ind = vec3(i,j,k);
                    if (is_deleted_fast(ind)) continue;

                    xxx = coords(ind);
                    if (bit.point_in(xxx)) {
                        mark_deleted_fast(ind);
                    }
                }
            }
        }
    }

    bool line_intersects(vec3 subgrid_index, vec3ff a, vec3ff b) {
        SubGridVolume &subg = subgrid[subgrid_index];

        if (line_intersect_plane(a, b, subg.bbox[0], subg.bbox[3], subg.bbox[7])) return true;
        if (line_intersect_plane(a, b, subg.bbox[0], subg.bbox[4], subg.bbox[7])) return true;

        if (line_intersect_plane(a, b, subg.bbox[1], subg.bbox[6], subg.bbox[5])) return true;
        if (line_intersect_plane(a, b, subg.bbox[1], subg.bbox[4], subg.bbox[6])) return true;

        if (line_intersect_plane(a, b, subg.bbox[0], subg.bbox[1], subg.bbox[4])) return true;
        if (line_intersect_plane(a, b, subg.bbox[0], subg.bbox[3], subg.bbox[4])) return true;

        if (line_intersect_plane(a, b, subg.bbox[7], subg.bbox[6], subg.bbox[5])) return true;
        if (line_intersect_plane(a, b, subg.bbox[7], subg.bbox[4], subg.bbox[5])) return true;

        if (line_intersect_plane(a, b, subg.bbox[4], subg.bbox[5], subg.bbox[1])) return true;
        if (line_intersect_plane(a, b, subg.bbox[4], subg.bbox[0], subg.bbox[1])) return true;

        if (line_intersect_plane(a, b, subg.bbox[3], subg.bbox[4], subg.bbox[6])) return true;
        if (line_intersect_plane(a, b, subg.bbox[3], subg.bbox[7], subg.bbox[6])) return true;
        return false;
    }

    void set_rotation(double _rotx) { rotx = _rotx; }
    double get_rotation() { return rotx; }

    inline void mark_deleted(vec3 const &ind) {
        //printf("deleting (%d, %d, %d)\n", ind.x, ind.y, ind.z);
        if (ind.x < -1) return;
        if (ind.y < -1) return;
        if (ind.z < -1) return;
        if (ind.x >= maxstep.x) return;
        if (ind.y >= maxstep.y) return;
        if (ind.z >= maxstep.z) return;
        mark_deleted_fast(ind);
    }

    inline int get_offset(int x, int y, int z) {
        //vec3 ind(x, y, z);
        //return get_offset(ind);
        return (x+1)*(maxyz) + (y+1)*(maxstep.z+2) + (z+1);
    }

    inline int get_offset(vec3 const &ind) {
        return (ind.x+1)*(maxyz) + (ind.y+1)*(maxstep.z+2) + (ind.z+1);
    }

    inline void mark_entrenched(vec3 const &ind) {
        vec3 tind;
        int offset;

        entrenched[get_offset(ind)] = false;

        tind = ind + vec3(-1, 0, 0);
        offset = get_offset(tind);
        if (!is_deleted(tind)) entrenched[offset] = false;

        tind = ind + vec3(-1, 0, -1);
        offset = get_offset(tind);
        if (!is_deleted(tind)) entrenched[offset] = false;

        tind = ind + vec3(0, 0, -1);
        offset = get_offset(tind);
        if (!is_deleted(tind)) entrenched[offset] = false;

        tind = ind + vec3(0, -1, 0);
        offset = get_offset(tind);
        if (!is_deleted(tind)) entrenched[offset] = false;

        tind = ind + vec3(-1, -1, 0);
        offset = get_offset(tind);
        if (!is_deleted(tind)) entrenched[offset] = false;

        tind = ind + vec3(-1, -1, -1);
        offset = get_offset(tind);
        if (!is_deleted(tind)) entrenched[offset] = false;

        tind = ind + vec3(0, -1, -1);
        offset = get_offset(tind);
        if (!is_deleted(tind)) entrenched[offset] = false;
    }

    inline void mark_deleted_fast(vec3 const &ind) {
        int offset = get_offset(ind);
        if (deleted[offset]) return;
        deleted[offset] = true;

        mark_entrenched(ind);

        vector<int> xlist, ylist, zlist;
        xlist.push_back(int(ind.x / substep.x) * substep.x);
        ylist.push_back(int(ind.y / substep.y) * substep.y);
        zlist.push_back(int(ind.z / substep.z) * substep.z);

        if (ind.x % substep.x == substep.x-1) {
            xlist.push_back(int(1 + ind.x / substep.x) * substep.x);
        }
        
        if (ind.y % substep.y == substep.y-1) {
            ylist.push_back(int(1 + ind.y / substep.y) * substep.y);
        }
        
        if (ind.z % substep.z == substep.z-1) {
            zlist.push_back(int(1 + ind.z / substep.z) * substep.z);
        }
        
        vec3 subind;
        BOOST_FOREACH(int x, xlist) {
            BOOST_FOREACH(int y, ylist) {
                BOOST_FOREACH(int z, zlist) {
                    subind = vec3(x, y, z);
                    SubGridVolumeMap::iterator it = subgrid.find(subind);
                    if (it != subgrid.end()) {
                        it->second.dirty = true;
                    }
                }
            }
        }
        dirty = true;
    }

    inline bool is_deleted(vec3 const &ind) {
        //log("Is deleted %d, %d, %d (%lu)", ind.x, ind.y, ind.z, deleted.size());
        if (ind.x < 0 || ind.y < 0 || ind.z < 0) return true;
        if (ind.x >= maxstep.x || ind.y >= maxstep.y || ind.z >= maxstep.z) return true;

        return deleted[get_offset(ind)];
    }
    
    inline bool is_deleted_fast(vec3 const &ind) {
        return deleted[get_offset(ind)];
    }

    inline bool is_entrenched(vec3 const &ind) {
        if (ind.x < 0 || ind.y < 0 || ind.z < 0) return true;
        if (ind.x >= maxstep.x || ind.y >= maxstep.y || ind.z >= maxstep.z) return true;

        return entrenched[get_offset(ind)];
    }

    inline bool is_entrenched_fast(vec3 const &ind) {
        return entrenched[get_offset(ind)];
    }
    
    template<class T>
    inline vec3ff coords(T &index) {
        return vec3ff(start.x + index.x*resolution, 
                     start.y + index.y*resolution, 
                     (start.z + index.z*resolution));
    }

    inline vec3 index(vec3ff &coords) {
        return vec3((coords.x - start.x)/resolution,
                    (coords.y - start.y)/resolution,
                    (coords.z - start.z)/resolution);
    }

    inline void linear_interp(vec3 v1, vec3 v2, vec3ff &res) {
        vec3ff c1 = coords(v1);
        vec3ff c2 = coords(v2);
        res = (c1 + c2) / 2.0;
        //res.v[0] = (c1.x + c2.x)/2;
        //res.v[1] = (c1.y + c2.y)/2;
        //res.v[2] = (c1.z + c2.z)/2;
    }    

public:  // make private later
    double resolution, rotx;
    vec3ff start, bounds;
    vec3 maxstep;
    bool dirty, calculating, needs_refresh;
    int maxyz;
    vec3 substep;
    SubGridVolumeMap subgrid;
    
    vector<bool> deleted;
    vector<bool> entrenched;
    boost::mutex gl_mutex;
};

