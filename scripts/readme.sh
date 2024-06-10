#!/bin/sh

# Tries to follow the steps of README.md closely, which helps to keep that file
# up-to-date.

set -ex

tmpdir=$(mktemp -d)

cat >logcabin-1.conf << EOF
serverId = 1
listenAddresses = 127.0.0.1:5254
storagePath=$tmpdir
EOF

cat >logcabin-2.conf << EOF
serverId = 2
listenAddresses = 127.0.0.1:5255
storagePath=$tmpdir
EOF

cat >logcabin-3.conf << EOF
serverId = 3
listenAddresses = 127.0.0.1:5256
storagePath=$tmpdir
EOF

mkdir -p debug

build/LogCabin --config logcabin-1.conf --bootstrap

build/LogCabin --config logcabin-1.conf --log debug/1 &
pid1=$!

build/LogCabin --config logcabin-2.conf --log debug/2 &
pid2=$!

build/LogCabin --config logcabin-3.conf --log debug/3 &
pid3=$!

ALLSERVERS=127.0.0.1:5254,127.0.0.1:5255,127.0.0.1:5256
build/Examples/Reconfigure --cluster=$ALLSERVERS set 127.0.0.1:5254 127.0.0.1:5255 127.0.0.1:5256

build/Examples/HelloWorld --cluster=$ALLSERVERS

# Alex Tsagkas Folder
build/Examples/TreeOps --cluster=$ALLSERVERS mkdir /alextsagkas/

echo "This is my first file." | \
build/Examples/TreeOps --cluster=$ALLSERVERS --dir=/alextsagkas/ write file_1.txt
echo "This is my second file." | \
build/Examples/TreeOps --cluster=$ALLSERVERS --dir=/alextsagkas/ write file_2.txt

# Angelor Motsios Folder
build/Examples/TreeOps --cluster=$ALLSERVERS mkdir /angelos_motsios/

echo "This is my 1st file." | \
build/Examples/TreeOps --cluster=$ALLSERVERS --dir=/angelos_motsios/ write file_1.txt
echo "This is my 2nd file." | \
build/Examples/TreeOps --cluster=$ALLSERVERS --dir=/angelos_motsios/ write file_2.txt
echo "This is my last word. I promise." | \
build/Examples/TreeOps --cluster=$ALLSERVERS --dir=/angelos_motsios/ write file_2.txt

# List all files in the root directory
build/Examples/TreeOps --cluster=$ALLSERVERS dump

kill $pid1
kill $pid2
kill $pid3

wait

rm -r $tmpdir
rm logcabin-1.conf logcabin-2.conf logcabin-3.conf
