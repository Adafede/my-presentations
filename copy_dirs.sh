#!/bin/bash

for d in */; do
  [ "$d" != "_site/" ] && cp -r "$d" "_site/$d"
done
