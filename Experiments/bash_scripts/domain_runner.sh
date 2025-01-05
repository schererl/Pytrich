#!/bin/bash

export PYTHONPATH=$PYTHONPATH:$(pwd)/Pytrich

# Check if domain folder argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <domain_folder>"
    exit 1
fi

# Set the domain directory from the terminal argument
domain_dir="$1"

# Define time and memory limits
TIME_LIMIT=300
MEM_LIMIT=8008608

# Define the array of domains to be ignored (optional)
ignored_domains=("Barman" "Freecell-Learned-ECAI-16" "ipc2020-feature-tests" "Logistics-Learned-ECAI-16" "SCCTEST")

# Define experiments as an array of associative arrays
declare -A experiments

experiments[0,name]="LMCOUNT-update"
experiments[0,command]='python3 ../../__main__.py "$domain_file" "$problem_file" -e "LMCOUNT-update" -N "AstarNode(G=1,H=5)" -S "Astar(use_early=True)" -H "LMCOUNT(use_bid=False, use_bu_update=True)" '

experiments[1,name]="TDG-satis"
experiments[1,command]='python3 ../../__main__.py "$domain_file" "$problem_file" -e "TDG-satis" -N "AstarNode(G=1,H=5)" -S "Astar(use_early=True)" -H "TDG(use_satis=True)" '

experiments[2,name]="TDG-LMCOUNT"
experiments[2,command]='python3 ../../__main__.py "$domain_file" "$problem_file" -e "TDG-LMCOUNT" -N "TiebreakingNode(G=1,H=5)" -S "Astar(use_early=True)" -A "Tiebreaking([TDG(use_satis=True),LMCOUNT(use_bu_update=True)])" '

experiments[3,name]="TDG-LMCOUNT-NOVELTY"
experiments[3,command]='python3 ../../__main__.py "$domain_file" "$problem_file" -e "TDG-LMCOUNT-NOVELTY" -N "TiebreakingNode(G=1,H=5)" -S "Astar(use_early=True)" -A "Tiebreaking([TDG(use_satis=True),LMCOUNT(use_bu_update=True), NOVELTY()])" '

experiments[4,name]="LMCOUNT-TDG"
experiments[4,command]='python3 ../../__main__.py "$domain_file" "$problem_file" -e "LMCOUNT-TDG" -N "TiebreakingNode(G=1,H=5)" -S "Astar(use_early=True)" -A "Tiebreaking([LMCOUNT(use_bu_update=True),TDG(use_satis=True)])" '

experiments[5,name]="LMCOUNT-TDG-NOVELTY"
experiments[5,command]='python3 ../../__main__.py "$domain_file" "$problem_file" -e "LMCOUNT-TDG-NOVELTY" -N "TiebreakingNode(G=1,H=5)" -S "Astar(use_early=True)" -A "Tiebreaking([LMCOUNT(use_bu_update=True),TDG(use_satis=True),NOVELTY()])" '


# Check if the domain directory exists
if [ -d "$domain_dir" ]; then
    # Extract the domain name from the directory path
    domain_name=$(basename "$domain_dir")
    # Check if the domain is in the ignored list
    if [[ " ${ignored_domains[@]} " =~ " ${domain_name} " ]]; then
        echo "Skipping ignored domain: $domain_name"
        exit 0
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
                    
                    
                    (
                        ulimit -t $TIME_LIMIT
                        ulimit -v $MEM_LIMIT
                        eval $experiment_command
                    )
                    echo "@"
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
                        
                        
                        (
                            ulimit -t $TIME_LIMIT
                            ulimit -v $MEM_LIMIT
                            eval $experiment_command
                        )
                        echo "@"
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
else
    echo "Domain directory does not exist: $domain_dir"
    exit 1
fi
