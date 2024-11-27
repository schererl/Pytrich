#!/bin/bash

export PYTHONPATH=$PYTHONPATH:$(pwd)/Pytrich

# Check if benchmark folder argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <benchmark_folder>"
    exit 1
fi

# Set the folder containing the benchmarks from the terminal argument
folder_benchmarks="$1/*"

# Define time and memory limits
TIME_LIMIT=1
MEM_LIMIT=8008608

# Define the array of domains to be ignored
ignored_domains=("Barman" "Freecell-Learned-ECAI-16" "ipc2020-feature-tests" "Logistics-Learned-ECAI-16" "SCCTEST")

# Define experiments as an array of associative arrays
declare -A experiments

# Experiment 1: NOVELTY
experiments[0,name]="NOVELTY"
experiments[0,command]='python3 ../../__main__.py "$domain_file" "$problem_file" -s Blind -sp "use_novelty=True"'

# Experiment 2: BLIND
experiments[1,name]="BLIND"
experiments[1,command]='python3 ../../__main__.py "$domain_file" "$problem_file" -s Blind -sp "use_novelty=False"'

# Experiment 3: LMCOUNT
experiments[2,name]="LMCOUNT"
experiments[2,command]='python3 ../../__main__.py "$domain_file" "$problem_file" -s Astar -H LMCOUNT'

# Add or remove experiments by modifying the experiments array
# Example of adding a new experiment:
# experiments[3,name]="NEW_EXPERIMENT"
# experiments[3,command]='python3 ../__main__.py "$domain_file" "$problem_file" -s NewSearch -H NewHeuristic'

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
                
                # Loop over experiments
                for i in "${!experiments[@]}"; do
                    # Only proceed if the key ends with 'name'
                    if [[ $i == *,name ]]; then
                        index=${i%,*}
                        experiment_name=${experiments[$index,name]}
                        experiment_command=${experiments[$index,command]}
                        
                        echo "@"
                        echo "Experiment name: $experiment_name"
                        echo "Domain name: $domain_file"
                        echo "Problem name: $problem_name"
                        (
                            ulimit -t $TIME_LIMIT
                            ulimit -v $MEM_LIMIT
                            eval $experiment_command
                        )
                    fi
                done
                
                # Clean up generated files
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
            for domain_file in "${domain_files[@]}"; do
                base_name=$(basename "$domain_file" | sed 's/-domain-grounded.hddl$//;s/-domain.hddl$//')
                corresponding_problems=($(find "$domain_dir" -maxdepth 1 -type f -name "${base_name}.hddl" ! -name "*-domain*"))
                for problem_file in "${corresponding_problems[@]}"; do
                    problem_name=$(basename "$problem_file")
                    
                    # Loop over experiments
                    for i in "${!experiments[@]}"; do
                        # Only proceed if the key ends with 'name'
                        if [[ $i == *,name ]]; then
                            index=${i%,*}
                            experiment_name=${experiments[$index,name]}
                            experiment_command=${experiments[$index,command]}
                            
                            echo "@"
                            echo "Experiment name: $experiment_name"
                            echo "Domain name: $domain_file"
                            echo "Problem name: $problem_name"
                            (
                                ulimit -t $TIME_LIMIT
                                ulimit -v $MEM_LIMIT
                                eval $experiment_command
                            )
                        fi
                    done
                    
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
