mkdir -p lib/tcltk
cp -r ~/lib/tcltk/*gz ./lib/tcltk/
rsync --delete -av ~/lib/mygl/ ./lib/mygl/
rsync --delete -av ~/lib/cpptk/ ./lib/cpptk/
find . -name "*.o" -exec rm \{\} \;
find . -name "*.d" -exec rm \{\} \;
docker build . -t cadcam:latest 
