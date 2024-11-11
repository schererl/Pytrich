#!/bin/bash

# Set the folder containing the benchmarks
folder_benchmarks="../htn-benchmarks/Blocksworld-GTOHP"

# Define time and memory limits
TIME_LIMIT=5
MEM_LIMIT=4000000

# Define the array of domains to be ignored
ignored_domains=("AssemblyHierarchical" "Childsnack" "Freecell-Learned-ECAI-16" "ipc2020-feature-tests" "Logistics-Learned-ECAI-16" "SCCTEST" "Woodworking")

# Iterate over each domain directory
for domain_dir in $folder_benchmarks; do
    if [ -d "$domain_dir" ]; then
        # Extract the domain name from the directory path
        domain_name=$(basename "$domain_dir")
        # Check if the domain is in the ignored list
        if [[ " ${ignored_domains[@]} " =~ " ${domain_name} " ]]; then
            echo "Skipping ignored domain: $domain_name"
            continue
        fi
        
        echo "Processing domain directory: $domain_dir"
        
        # Find all .hddl files, excluding those with '-grounded' in the name
        files=($(find "$domain_dir" -maxdepth 1 -type f -name "*.hddl" ! -iname "*-grounded*"))
        
        # Separate domain and problem files
        domain_files=()
        problem_files=()

        for file in "${files[@]}"; do
            if [[ "$(basename "$file")" == *domain* ]]; then
                domain_files+=("$file")
            else
                problem_files+=("$file")
            fi
        done

        # If there is only one domain file, use it for all problem files
        if [ ${#domain_files[@]} -eq 1 ]; then
            domain_file="${domain_files[0]}"
            for problem_file in "${problem_files[@]}"; do
                problem_name=$(basename "$problem_file")
                echo "@"
                echo "Running classical landmark experiment for $problem_name:"
                (
                    ulimit -t $TIME_LIMIT
                    ulimit -v $MEM_LIMIT
                    export PYTHONPATH=$PYTHONPATH:~/Desktop/Pytrich/Pytrich
                    python3 ../__main__.py -lge -hp "name=\"Classical Landmarks\", use_falm=False, use_bid=False, use_disj=True" "$domain_file" "$problem_file"
                )
                echo "@"
                echo "Running bidirectional landmark experiment for $problem_name:"
                (
                    ulimit -t $TIME_LIMIT
                    ulimit -v $MEM_LIMIT
                    export PYTHONPATH=$PYTHONPATH:~/Desktop/Pytrich/Pytrich
                    python3 ../__main__.py -lge -hp "name=\"Bidirectional Landmarks\",use_falm=False, use_bid=True, use_disj=True" "$domain_file" "$problem_file"
                )
                
                # Remove .psas files and panda.log from the current directory
                if ls ./*.psas 1> /dev/null 2>&1; then
                    rm ./*.psas
                fi

                if [ -f ./panda.log ]; then
                    rm ./panda.log
                fi

            done
        else
            domain_files=($(find "$domain_dir" -maxdepth 1 -type f -name "*-domain.hddl" -o -name "*-domain-grounded.hddl"))
            # If there are multiple domain files, pair them with corresponding problem files
            echo "$domain_file"
            for domain_file in "${domain_files[@]}"; do
                base_name=$(basename "$domain_file" | sed 's/-domain-grounded.hddl$//;s/-domain.hddl$//')
                corresponding_problems=($(find "$domain_dir" -maxdepth 1 -type f -name "${base_name}.hddl" ! -name "*-domain*"))
                for problem_file in "${corresponding_problems[@]}"; do
                    problem_name=$(basename "$problem_file")
                    
                    echo "@"
                    echo "$domain_file"
                    echo "$problem_file"
                    echo "Running classical landmark experiment for $problem_name:"
                    (
                        ulimit -t $TIME_LIMIT
                        ulimit -v $MEM_LIMIT
                        python3 ../__main__.py -lge -hp "use_falm=False, use_bid=False, use_disj=True" "$domain_file" "$problem_file"
                    )
                    echo "@"
                    echo "Running bidirectional landmark experiment for $problem_name:"
                    (
                        ulimit -t $TIME_LIMIT
                        ulimit -v $MEM_LIMIT
                        python3 ../__main__.py -lge -hp "use_falm=False, use_bid=True, use_disj=True" "$domain_file" "$problem_file"
                    )
                    
                    # Clean up generated files
                    if ls ./*.psas 1> /dev/null 2>&1; then
                        rm ./*.psas
                    fi

                    if [ -f ./panda.log ]; then
                        rm ./panda.log
                    fi
                done
            done
            
        fi
    fi
done
