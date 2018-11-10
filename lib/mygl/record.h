#pragma once

#include "opencv/highgui.h"
#include "opencv/cv.h"

#include <string>

#include "mygl.h"

//using namespace std;

void save_frame(cv::VideoWriter &writer, int width, int height) {
    //printf("Writing frame...\n");
    cv::Mat img(height, width, CV_8UC3);
    glPixelStorei(GL_PACK_ALIGNMENT, (img.step & 3)?1:4);
    glPixelStorei(GL_PACK_ROW_LENGTH, img.step/img.elemSize());
    glReadPixels(0, 0, img.cols, img.rows, GL_BGR_EXT, GL_UNSIGNED_BYTE, img.data);
    cv::Mat flipped(img);
    cv::flip(img, flipped, 0);
    writer << img;
}
