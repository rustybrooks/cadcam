#include "path.h"

#include "canon.h"
#include "interface.h"
#include "rs274ngc.h"
#include "rs274ngc_return.h"
#include "sim_time.h"

#include <fstream>
#include <sstream>
#include <string>

#include <boost/tokenizer.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/foreach.hpp>


void report_error(int error_code,                                   /* the code number of the error message */
                  int print_stack)                                  /* print stack if ON, otherwise not     */
{
    char buffer[RS274NGC_TEXT_SIZE];
    int k;

    rs274ngc_error_text(error_code, buffer, 5);   /* for coverage of code */
    rs274ngc_error_text(error_code, buffer, RS274NGC_TEXT_SIZE);
    fprintf(stderr, "%s\n",
            ((buffer[0] IS 0) ? "Unknown error, bad error code" : buffer));
    rs274ngc_line_text(buffer, RS274NGC_TEXT_SIZE);
    fprintf(stderr, "%s\n", buffer);
    if (print_stack IS ON)
        {
            for (k=0; ; k++)
                {
                    rs274ngc_stack_name(k, buffer, RS274NGC_TEXT_SIZE);
                    if (buffer[0] ISNT 0)
                        fprintf(stderr, "%s\n", buffer);
                    else
                        break;
                }
        }
}

bool parse_gcode_comment(std::string line, vector<double> &stock_args, Bit *b) {
    vector< string > vec;
    boost::char_separator<char> sep(" ()[]=,");
    bool have_stock = false;

    boost::tokenizer<boost::char_separator<char> >tok(line, sep);
    vec.assign(tok.begin(), tok.end());
    //fprintf(stderr, "vec[0] = %s\n", vec[0].c_str());
    if (vec[0] == "RectSolid") {
        stock_args.resize(6);
        stock_args[0] = boost::lexical_cast<double>(vec[1]);
        stock_args[1] = boost::lexical_cast<double>(vec[2]);
        stock_args[2] = boost::lexical_cast<double>(vec[3]);
        stock_args[3] = boost::lexical_cast<double>(vec[5]);
        stock_args[4] = boost::lexical_cast<double>(vec[6]);
        stock_args[5] = boost::lexical_cast<double>(vec[7]);
        have_stock = true;
    } else if (vec[0] == "VMill") {
        fprintf(stderr, "Setting to VMill\n");
        double length = boost::lexical_cast<double>(vec[1]);
        double radius = boost::lexical_cast<double>(vec[2]);
        double included_angle = boost::lexical_cast<double>(vec[3]);
        double height = radius / tan(DEG2RAD*included_angle/2.0);

        b->clear();
        b->add(new BitCylinder(height, length-height, radius));
        b->add(new BitCone(0, height, 1/1000., radius));
    } else if (vec[0] == "BallMill") {
        fprintf(stderr, "Setting to BallMill\n");
        double length = boost::lexical_cast<double>(vec[1]);
        double radius = boost::lexical_cast<double>(vec[2]);

        b->clear();
        b->add(new BitCylinder(radius, length-radius, radius));
        b->add(new BitSphere(radius, radius));
    } else if (vec[0] == "FlatMill") {
        fprintf(stderr, "Setting to FlatMill\n");
        double length = boost::lexical_cast<double>(vec[1]);
        double radius = boost::lexical_cast<double>(vec[2]);

        b->clear();
        b->add(new BitCylinder(0, length, radius));
    }

    return have_stock;
}

bool extract_gcode_args(std::string filename, std::vector<double> &stock_args, Bit *b) {
    ifstream in(filename.c_str());
    if (!in.is_open()) {
        printf("Count not open gcode file '%s", filename.c_str());
        return false;
    }

    string line;
    bool have_stock = false;

    while (getline(in,line)) {
        if (parse_gcode_comment(line, stock_args, b)) {
            have_stock = true;
        }
    }

    return have_stock;
}

GcodeFile *process_gcode_file(std::string filename) {
    int status = 0;
    int do_next = 0;                                      /* what to do if error        */
    int block_delete = 0;                                 /* switch which is ON or OFF  */
    int print_stack = 0;                                  /* option which is ON or OFF  */
    //int tool_flag;

    fprintf(stderr, "opening file... %s\n", filename.c_str());

    // FIXME I honestly don't remember why
    strcpy(_parameter_file_name, "./rs274ngc.var");

    if ((status = rs274ngc_init()) ISNT RS274NGC_OK) {
        report_error(status, print_stack);
        exit(1);
    }

    status = rs274ngc_open(filename.c_str());

    GcodeFile *gcfile = new GcodeFile(filename);
    set_gcode_file(gcfile);

    char gcode[5001];
    while (true) {
        status = rs274ngc_read(NULL);
        rs274ngc_line_text(gcode, 5000);
        gcfile->add(gcode);
        gui_interface::add_gcode_line(gcfile->current());

        if ((status IS RS274NGC_EXECUTE_FINISH) AND (block_delete IS ON)) {
            continue;
        } else if (status IS RS274NGC_ENDFILE) {
            break;
        }

        if ((status ISNT RS274NGC_OK) AND (status ISNT RS274NGC_EXECUTE_FINISH)) { // should not be EXIT
            report_error(status, print_stack);
            if ((status IS NCE_FILE_ENDED_WITH_NO_PERCENT_SIGN) OR  (do_next IS 2)) { /* 2 means stop */
                status = 1;
                break;
            } else if (do_next IS 1) {               /* 1 means MDI */
                continue;
            } else                                   /* 0 means continue */
                continue;
        }

        status = rs274ngc_execute();
        if ((status ISNT RS274NGC_OK) AND
            (status ISNT RS274NGC_EXIT) AND
            (status ISNT RS274NGC_EXECUTE_FINISH)) {
                report_error(status, print_stack);
                status = 1;
                if (do_next IS 1) {                  /* 1 means MDI */
                } else if (do_next IS 2) {           /* 2 means stop */
                    break;
                }
        } else if (status IS RS274NGC_EXIT) {
            break;
        }
    }

    gui_interface::tk_update();
    set_gcode_file(NULL);

    gcfile->set_status(status);
    return gcfile;
}


