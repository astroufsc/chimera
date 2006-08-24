
which aclocal > /dev/null || "You don't have aclocal in your PATH."

echo -n "Running ";
aclocal --version | grep aclocal
aclocal

echo -n "Running ";
autoheader --version | grep autoheader
autoheader

echo -n "Running ";
autoconf --version | grep autoconf
autoconf

echo -n "Running ";
automake --version | grep automake
automake -a

echo "Now, run ./configure, then, make and make install."

