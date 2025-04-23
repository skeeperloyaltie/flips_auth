#!/bin/bash

# Loop 100 times
for i in {1..100}
do
    echo "Running migration attempt $i"
    python manage.py migrate datasync
    
    # If the command exits with a non-zero status, break the loop
    if [ $? -ne 0 ]; then
        echo "Migration failed on attempt $i"
        break
    fi
done
