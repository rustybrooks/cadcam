//#include "opencv/highgui.h"
//#include "opencv/cv.h"

#include "opencv2/opencv.hpp"

#include <boost/lexical_cast.hpp>
#include <boost/program_options.hpp>
#include <boost/foreach.hpp>

#include <sys/time.h>
#include <iostream>

namespace po = boost::program_options;

//using namespace std;
//using namespace cv;

using std::cout;
using std::endl;
using std::string;

using cv::Mat;
using cv::namedWindow;
using cv::VideoCapture;
using cv::waitKey;

string input_file;

Mat rotate90(Mat img) {
  Mat img90;
  transpose(img, img90);  
  flip(img90, img90, 1); //transpose+flip(1)=CW
  return img90;
}

double time() {
    struct timeval ts;
    gettimeofday(&ts, NULL);
    return ts.tv_sec + ts.tv_usec/1e6;
}

int main(int argc, char *argv[]) {
    po::options_description desc("Allowed options");
    desc.add_options()
        ("help,h", "produce help message")
        ("input-file,i", po::value<string>(&input_file), "")
        ;

    po::positional_options_description p;
    p.add("input-file", 1);

    po::variables_map vm;
    po::store(po::command_line_parser(argc, argv).options(desc).positional(p).run(), vm);
    string config_file(input_file + ".cfg");
    po::notify(vm);

    if (vm.count("help")) {
        cout << desc << "\n";
        return 1;
    }

    VideoCapture cap;

    if (input_file.size() == 0) {
	    cap.open(0);
    } else {
	    cap.open(input_file);
    }

    if (!cap.isOpened()) {
	    fprintf(stderr, "Couldn't open file %s\n", input_file.c_str());
	    return 1;
    }

    Mat frame, display_scaled;

    cap >> frame;

    bool rotate = false;

    int width, height;
    if (rotate) {
        height = cap.get(CV_CAP_PROP_FRAME_WIDTH);
        width = cap.get(CV_CAP_PROP_FRAME_HEIGHT);
    } else {
        width = cap.get(CV_CAP_PROP_FRAME_WIDTH);
        height = cap.get(CV_CAP_PROP_FRAME_HEIGHT);
    }

    printf("Video dimension = %d x %d\n", width, height);

    namedWindow("foo", CV_WINDOW_AUTOSIZE);

    int fnum=0;
    double start_time = time();

    while (cap.read(frame)) {
        fnum++;
        if (rotate) frame = rotate90(frame);

        imshow("foo", frame);

        if (fnum % 120 == 0) {
            printf("Frame %d, fps=%0.2f\n", fnum, fnum/(time()-start_time));
        }

        if(waitKey(1) == 27) { //wait for 'esc' key press for 30 ms. If 'esc' key is pressed, break loop
            cout << "esc key is pressed by user" << endl;
            break;
        }
    }
}
