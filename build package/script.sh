ls
rm -rf ./debian
mkdir -p ./debian/usr/bin
cp simeis ./debian/usr/bin
mkdir -p debian/DEBIAN
find ./debian -type d | xargs chmod 755
cp control debian/DEBIAN
chmod 644 ./debian/DEBIAN/control
dpkg-deb --build debian dpkg-deb: building package `simeis' in `debian.deb'.
mv debian.deb simeis_0.0.0-rc0_all.deb
root# dpkg -i ./simeis_0.0.0-rc0_all.deb