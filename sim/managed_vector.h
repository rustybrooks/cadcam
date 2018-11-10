#ifndef __managed_vector_h
#define __managed_vector_h

#include <vector>

//using namespace std;

template<class T> 
class ManagedVector {
public:
    typedef vector<T> vec_type;
    ManagedVector(int bin_size)
        : _bin_size(bin_size)
        , _segments(0)
        , _size(0)
    {}

    void clear() {
        typename std::vector<T>::iterator it, end=_vectors.end();
        _size = 0;
        for (it=_vectors.begin(); it!=end; it++) {
            it->clear();
        }
    }

    void add_segment() {
        vec_type tmp;
        tmp.reserve(_bin_size);
        _vectors.push_back(tmp);
        _segments++;
    }

    void add_filled_segment(T const &val) {
        vec_type tmp = vector<T>(_bin_size, val);
        _vectors.push_back(tmp);
        _segments++;
        _size += _bin_size;
    }

    void reserve(int sz) {
        while (_segments*_bin_size < sz) {
            add_segment();
        }
    }

    void push_back(T const &val) {
        int segment = _size/_bin_size;
        if (segment > _segments) add_segment();
        _vectors[_size/_bin_size].push_back(val);
        _size++;
    }

    void resize(size_t sz) {
        // do nothing
    }

    inline T &operator[] (size_t n) {
        while (n >= _size) add_filled_segment(0);
        return _vectors[n/_bin_size][n % _bin_size];
    }

    vector<T> &get_segment(int seg) {
        return _vectors[seg];
    }

    inline size_t segments() const { return _segments; }
    inline size_t bin_size() const { return _bin_size; }
    inline size_t size() const { return _size; }

private:
    size_t _bin_size, _segments, _size;
    vector<vec_type> _vectors;
};

#endif // __managed_vector_h
