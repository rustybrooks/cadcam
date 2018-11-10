//#define _USE_MATH_DEFINES
//#include <cmath>

#pragma once

#include "math_funcs.h"
#include "shader.h"

#include <memory>
#include <string>
#include <cstring>
#include <boost/unordered_map.hpp>

const vec3ff VX(1,0,0);
const vec3ff VY(0,1,0);
const vec3ff VZ(0,0,-1);

extern boost::unordered_map<int, bool> gl_keyStates;
extern boost::unordered_map<int, bool> gl_mouseStates;

class Camera {

public:
    Camera(double _width, double _height, double _fov=25.0) 
        : dirty(false)
        , fix_y(true)
        , last_mouse_x(-1)
        , last_mouse_y(-1)
        , fov(_fov)
        , position(vec3ff(0, 0, 0))
        , block_id(0)
        , cam_block_buffer(0)
    {
        view_mat = identity_mat4();

        set_dimensions(_width, _height);

        create_versor(quaternion, 0.0, 0.0f, 1.0f, 0.0f);
        quat_to_mat4(R.m, quaternion);

        forward = vec4(0.0f, 0.0f, -1.0f, 0.0f);
        right = vec4(1.0f, 0.0f, 0.0f, 0.0f);
        up = vec4(0.0f, 1.0f, 0.0f, 0.0f);
    }

    int get_width() { return win_width; }
    int get_height() { return win_height; }


    void bind() {
        glGenBuffers(1, &cam_block_buffer); 
        glBindBuffer(GL_UNIFORM_BUFFER, cam_block_buffer);
        glBufferData(GL_UNIFORM_BUFFER, sizeof (float) * 32, NULL, GL_DYNAMIC_DRAW);
    }

    void set_view_matrix(mat4 view) {
        view_mat = view;
    }

    void set_position(vec3ff pos) {
        dirty=true;
        position = pos;
    }

    void set_dimensions(int width, int height) {
        win_width = width;
        win_height = height;
        set_projection(win_width / win_height, 0.1, 1000, fov);
    }

    void set_fov(double _fov) {
        fov = _fov;
        set_projection(win_width / win_height, 0.1, 1000, fov);
    }

    void process_controls_standard(float cam_speed, float cam_heading_speed, float elapsed_seconds) {
        // move to the right
        if (gl_keyStates[GLFW_KEY_A]) {
            move_right(-cam_speed*elapsed_seconds);
        }

        // move to the left        
        if (gl_keyStates[GLFW_KEY_D]) {
            move_right(cam_speed*elapsed_seconds);
        }
        
        // move up
        if (gl_keyStates[GLFW_KEY_Q]) {
            move_up(cam_speed*elapsed_seconds);
        }

        // move down
	if (gl_keyStates[GLFW_KEY_E]) {
            move_up(-cam_speed*elapsed_seconds);
        }

        // move forward
	if (gl_keyStates[GLFW_KEY_W]) {
            move_forward(cam_speed*elapsed_seconds);
        }

        // move backward
        if (gl_keyStates[GLFW_KEY_S]) {
            move_forward(-cam_speed*elapsed_seconds);
        }
        
	// roll left
        if (gl_keyStates[GLFW_KEY_Z]) {
            rotate_roll(-cam_heading_speed * elapsed_seconds);
        }

	// roll right
        if (gl_keyStates[GLFW_KEY_C]) {
            rotate_roll(cam_heading_speed * elapsed_seconds);
        }

	// yaw left
        if (gl_keyStates[GLFW_KEY_J]) {
            rotate_yaw(-cam_heading_speed * elapsed_seconds);
        }

	// yaw right
        if (gl_keyStates[GLFW_KEY_L]) {
            rotate_yaw(cam_heading_speed * elapsed_seconds);
        }

	// pitch up
        if (gl_keyStates[GLFW_KEY_I]) {
            rotate_pitch(cam_heading_speed * elapsed_seconds);
        }

	// pitch down
        if (gl_keyStates[GLFW_KEY_K]) {
            rotate_pitch(-cam_heading_speed * elapsed_seconds);
        }

        if (gl_mouseStates[GLFW_MOUSE_BUTTON_MIDDLE]) {
            double x, y;
            glfwGetCursorPos(g_window, &x, &y);
            if (last_mouse_x!=-1) {
                double yawdiff = (x-last_mouse_x)/-4.0;
                double pitchdiff = (y-last_mouse_y)/-4.0;
                rotate_pitch(pitchdiff);
                rotate_yaw(yawdiff);
            }
            
            if (x > win_width or x<50 or y>win_height or y<50) {
                glfwSetCursorPos(g_window, win_width/2.0, win_height/2.0);
                last_mouse_x=win_width/2; last_mouse_y=win_height/2;
            } else {
                last_mouse_x=x; last_mouse_y=y;
            }
        }
    }


    void rotate(vec4 &axis, float change) {
        float q[16];
        create_versor(q, change, axis.v[0], axis.v[1], axis.v[2]);
        mult_quat_quat (quaternion, q, quaternion);

        quat_to_mat4 (R.m, quaternion);
        forward = R * vec4(0.0, 0.0, -1.0, 0.0);
        right = R * vec4(1.0, 0.0, 0.0, 0.0);
        up = R * vec4(0.0, 1.0, 0.0, 0.0);
    }

    void rotate_yaw(double change) {
        yaw -= change;
        if (fix_y) {
            vec4 y(0.0f, 1.0f, 0.0f, 0.0f);
            rotate(y, change);
        } else {
            rotate(up, change);
        }
	fprintf(stderr, "yaw = %f\n", yaw);
        dirty = true;
    }

    void rotate_pitch(double change) {
        pitch -= change;
        rotate(right, change);
	fprintf(stderr, "pitch = %f\n", pitch);
        dirty = true;
    }

    void rotate_roll(double change) {
        roll -= change;
        rotate(forward, change);
        dirty=true;
    }

    bool is_dirty() {
        return dirty;
    }

    // for some reason mingw c++ does not like the variable named near or far
    void set_projection(double aspect, double nearx=0.1, double farx=1000.0, double fov=67.0) {
        double fov_rad = fov * DEG2RAD;
	double top = nearx*tan(fov_rad/2.0f);
	double bottom = -top;
	double right = top*aspect;
	double left = -right;


	double sx = (2*nearx) / (right-left);
        double sy = (2*nearx) / (top-bottom);
        double sz = -1 * (farx+nearx) / (farx-nearx);
        double pz = (-2*farx*nearx) / (farx - nearx);
        //printf("perspective fov=%f, range=%f\n", fov_rad, range);
	proj_mat = mat4(
 	    sx, 0,   0,   0,
	    0,  sy,  0,   0,
	    0,  0,   sz,  -1,
	    0,  0,   pz,   0
	);
	/*
        double range = tan(fov_rad / 2.0f) * nearx;
        double fov_rad = fov * DEG2RAD;
        double range = tan(fov_rad / 2.0f) * nearx;
        double sx = (2.0f * nearx) / (range * aspect + range * aspect);
        double sy = nearx / range;
        double sz = -(farx + nearx) / (farx - nearx);
        double pz = -(2.0f * farx * nearx) / (farx - nearx);
        mat4 m = zero_mat4(); // make sure bottom-right corner is zero
        m.m[0] = sx;
        m.m[5] = sy;
        m.m[10] = sz;
        m.m[14] = pz;
        m.m[11] = -1.0f;

        proj_mat = m;
	*/
        //proj_mat = perspective(fov, aspect, nearx, farx);
    }

    void set_ortho(double left, double bottom, double right, double top, double farx=10000, double nearx=-10000) {
        proj_mat = mat4(
                        2.0 / (right - left), 0,                    0, 0,
                        0,                    2.0 / (top - bottom), 0, 0,
                        0,                    0,                    -2.0 / (farx - nearx), 0,
                        -(right + left) / (right - left), -(top + bottom) / (top - bottom), -(farx + nearx) / (farx - nearx), 1
                        );

    }

 

    float *view_matrix() {
        if (dirty) {
            quat_to_mat4(R.m, quaternion);
            T = translate(identity_mat4(), position);
			
            view_mat = inverse(R) * inverse(T);

            dirty = false;
        }

        return view_mat.m;
    }

    void move_axis(const vec4 &axis, float distance) {
        dirty = true;

        position = position + vec3ff(axis) * distance;
    }

    void move_right(float distance) {
        move_axis(right, distance);
    }

    void move_forward(float distance) {
        move_axis(forward, distance);
    }

    void move_up(float distance) {
        move_axis(up, distance);
    }

    float *proj_matrix() {
        return proj_mat.m;
    }

    void update_uniform_block() {
        glBindBufferBase(GL_UNIFORM_BUFFER, block_id, cam_block_buffer); 
        cam_ubo_ptr = (float*) glMapBufferRange ( 
            GL_UNIFORM_BUFFER, 
            0, 
            sizeof (float) * 32, 
            GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT 
            ); 
	std::memcpy (&cam_ubo_ptr[0], proj_matrix(), sizeof(float) * 16); 
	std::memcpy (&cam_ubo_ptr[16], view_matrix(), sizeof(float) * 16); 
        glUnmapBuffer(GL_UNIFORM_BUFFER);
    }

    void register_shader(ShaderProgram &s) {
        GLuint bindex = glGetUniformBlockIndex(s.program(), "cam_block"); 
        glUniformBlockBinding(s.program(), bindex, block_id); 
    }

/* create a unit quaternion q from an angle in degrees a, and an axis x,y,z */
void create_versor (float* q, float a, float x, float y, float z) {
	float rad = DEG2RAD * a;
	q[0] = cosf(rad / 2.0f);
	q[1] = sinf(rad / 2.0f) * x;
	q[2] = sinf(rad / 2.0f) * y;
	q[3] = sinf(rad / 2.0f) * z;
}

/* multiply quaternions to get another one. result=R*S */
void mult_quat_quat (float* result, float* r, float* s) {
	result[0] = s[0] * r[0] - s[1] * r[1] -
            s[2] * r[2] - s[3] * r[3];
	result[1] = s[0] * r[1] + s[1] * r[0] -
            s[2] * r[3] + s[3] * r[2];
	result[2] = s[0] * r[2] + s[1] * r[3] +
            s[2] * r[0] - s[3] * r[1];
	result[3] = s[0] * r[3] - s[1] * r[2] +
            s[2] * r[1] + s[3] * r[0];
	// re-normalise in case of mangling
	normalise_quat(result);
}

/* convert a unit quaternion q to a 4x4 matrix m */
void quat_to_mat4 (float* m, float* q) {
	float w = q[0];
	float x = q[1];
	float y = q[2];
	float z = q[3];
	m[0] = 1.0f - 2.0f * y * y - 2.0f * z * z;
	m[1] = 2.0f * x * y + 2.0f * w * z;
	m[2] = 2.0f * x * z - 2.0f * w * y;
	m[3] = 0.0f;
	m[4] = 2.0f * x * y - 2.0f * w * z;
	m[5] = 1.0f - 2.0f * x * x - 2.0f * z * z;
	m[6] = 2.0f * y * z + 2.0f * w * x;
	m[7] = 0.0f;
	m[8] = 2.0f * x * z + 2.0f * w * y;
	m[9] = 2.0f * y * z - 2.0f * w * x;
	m[10] = 1.0f - 2.0f * x * x - 2.0f * y * y;
	m[11] = 0.0f;
	m[12] = 0.0f;
	m[13] = 0.0f;
	m[14] = 0.0f;
	m[15] = 1.0f;
}

/* normalise a quaternion in case it got a bit mangled */
void normalise_quat (float* q) {
	// norm(q) = q / magnitude (q)
	// magnitude (q) = sqrt (w*w + x*x...)
	// only compute sqrt if interior sum != 1.0
	float sum = q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3];
	// NB: floats have min 6 digits of precision
	const float thresh = 0.0001f;
	if (fabs (1.0f - sum) < thresh) {
		return;
	}
	float mag = sqrt (sum);
	for (int i = 0; i < 4; i++) {
		q[i] = q[i] / mag;
	}
}

private:
    bool dirty, fix_y;
    
    float win_width, win_height, last_mouse_x, last_mouse_y;
    float fov;
    float quaternion[4];
    vec4 forward, right, up;
    mat4 R, T;

    double yaw, pitch, roll;
    //double zrot;
    vec3ff position;
    mat4 view_mat;
    mat4 proj_mat;
    int block_id; 
    GLuint cam_block_buffer; 
    float* cam_ubo_ptr;
};
