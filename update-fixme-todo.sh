find . -type f -name *.c -or -name *.py -or -name *.h -or -name *.cpp | xargs grep -n FIXME >> FIXME
find . -type f -name *.c -or -name *.py -or -name *.h -or -name *.cpp | xargs grep -n TODO >> TODO
