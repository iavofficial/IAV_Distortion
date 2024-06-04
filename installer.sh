#!/bin/bash

function request_directory() {
    # Ask for a directory, keep asking until an existing one is provided
    while true; do
        read -p "Enter the directory to clone the repository to (leave empty for current directory: $(pwd)): " dir

        # Use current directory if input is empty
        if [ -z "$dir" ]; then
            dir=$(pwd)
        fi

        # Check if the directory exists
        if [ -d "$dir" ]; then
            # Check if directory/repository already exists

            if [ -d "$dir/$repo_name" ] 
            then
                echo "The repository already exists. Do you want to overwrite it? "
                read -p $'\033[0;33mWARNING: This will delete everything in the directory.\033[0m (y/n) ' -n 1 -r	    
                echo    # move to a new line
                # If user decides to overwrite, remove the existing directory
                    if [[ $REPLY =~ ^[Yy]$ ]]
                    then
                        rm -rf "$dir/$repo_name"
                    else
                        echo "Aborting clone process."
                        exit 1
                    fi
                fi

            break  # exit the loop once a valid directory is entered
        else
            echo "The directory $dir does not exist. Please enter an existing directory."
        fi
    done
}

# Repository url
repo_url="https://github.com/iavofficial/IAV_Distortion.git"
# Extract repository name from the URL to check if it already exists
repo_name=$(basename $repo_url .git)

# search for existing copy of the repository
existing_copies=$(find .. -name $repo_name -not -path "*/.local/*")
copy_exists=0

for copy in $existing_copies
do
    let copy_exists=copy_exists+1
done

if [ $copy_exists -eq 1 ]
then
    echo "A directory called $repo_name already exists ($existing_copies). Do you want to overwrite it?"
    read -p $'\033[0;33mWARNING: This will delete everything in the directory.\033[0m (y/n) ' -n 1 -r
    echo    # move to a new line

    if [[ $REPLY =~ ^[Yy]$ ]]
    then    
        # Remove the directory (WARNING: THIS WILL DELETE EVERYTHING IN THE DIRECTORY!)        
        echo "Removing $existing_copies"
        rm -rf $existing_copies
        # go one level up for dir
        dir=$existing_copies
        # dir=$(dirname "$dir")
        echo "$repo_name will be cloned to: $dir"
    else
        echo -e "\033[0;33m Please make sure that you have no duplicates of IAV-Distortion running in parallel.\033[0m"
        request_directory
    fi

elif [[ $copy_exists -gt 1 ]]
then
    echo -e "\033[0;33mMultiple directories named IAV_Distortion have been found. Please make sure that you have no duplicates of IAV-Distortion running in parallel.\033[0m"
    for copy in $existing_copies
    do
        echo $copy
    done
    echo    # move to a new line
    request_directory
else
    request_directory
fi

# Ask for the branch to clone
read -p "Enter the branch you want to clone (leave empty for master): " branch
# Use 'master' if input is empty
if [ -z "$branch" ]; then
    branch='master'
fi

# Clone git repository to previous defined drirectory
git clone -b $branch $repo_url "$dir/$repo_name"

# Make all utility scripts in the /src directory executable
find "$dir/$repo_name" -type f -iname "*.sh" -exec chmod +x {} \;

# Ask if install script shall be executed
read -p "Do you want to run the install script? (y/n) " -n 1 -r
echo    # move to a new line
cd "$dir/$repo_name/src"

if [[ $REPLY =~ ^[Yy]$ ]]
then
    source install.sh
fi

# Wait for user input before closing
echo "Press any key to exit..."
read -n 1
