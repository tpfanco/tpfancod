#!/bin/bash
if [ "$1" = "pre" ]; then
  kill /usr/bin/tpdand
if [ "$1" = "post" ]; then
  kill /usr/bin/tpdand
