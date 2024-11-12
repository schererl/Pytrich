import subprocess
import os
from Pytrich.Grounder.sasplus_parser import SASPlusParser
import Pytrich.FLAGS as FLAGS
from Pytrich.model import AbstractTask, Decomposition, Fact, Model, Operator


class PandaGrounder:
    def __init__(self, sas_file=None, domain_file=None, problem_file=None):
        """
        Initializes the PandaGrounder.
        If `sas_file` is provided, grounding is skipped.
        Otherwise, `domain_file` and `problem_file` are required to perform grounding.
        """
        self.sas_file        = sas_file
        self.domain_file     = domain_file
        self.problem_file    = problem_file
        self.sasplus_parser  = None
        self.grounder_status = 'NOT_RUN'
        self.model = None
        
        # Validate that either sas_file is provided or both domain_file and problem_file are provided
        if not self.sas_file and (not self.domain_file or not self.problem_file):
            raise ValueError("Either `sas_file` or both `domain_file` and `problem_file` must be provided.")

    def __call__(self):
        """
        Runs the grounding process if needed, then parses the SAS file.
        """
        if not self.sas_file:
            # If sas_file is not provided, perform grounding
            self.sas_file = self._run_panda_grounding()
            if self.sas_file is None:
                print("Grounding failed.")
                return
        
        # Parse the SAS file to create the model
        self.sasplus_parser = SASPlusParser(self._read_sas_file())
        self.sasplus_parser.parse()
        return self._build_model()

    def _build_model(self):
        facts = [Fact(**fact_dict) for fact_dict in self.sasplus_parser.facts]
        operators = [Operator(**operator_dict) for operator_dict in self.sasplus_parser.operators]
        abstract_tasks = [AbstractTask(**abstract_task_dict) for abstract_task_dict in self.sasplus_parser.abstract_tasks] #NOTE: need to process decompositions
        decompositions = [Decomposition(**decomp_dict) for decomp_dict in self.sasplus_parser.decompositions] #NOTE: need to process subtasks and compound task
        #process decomposition's task network, and compound task's decompositions
        for d in decompositions:
            d.compound_task = abstract_tasks[d.compound_task['local_id']]
            d.compound_task.decompositions.append(d)
            for task_id, subt in enumerate(d.task_network):
                task_type, task_name = subt
                if task_type=='O':
                    d.task_network[task_id]=operators[task_name]
                else:
                    d.task_network[task_id]=abstract_tasks[task_name]
        #processs intial task network
        initial_task_network = [abstract_tasks[t['local_id']]  for t in self.sasplus_parser.initial_task_network]
        return Model(facts,
                    self.sasplus_parser.initial_state,
                    initial_task_network,
                    self.sasplus_parser.goals,
                    operators,
                    decompositions,
                    abstract_tasks)

    def _run_panda_grounding(self):
        """
        Run the panda grounding process on the provided domain and problem files.
        Returns the path to the generated SAS file if successful, otherwise None.
        """
        script_dir = os.path.dirname(__file__)
        pandaPIparser_path = os.path.join(script_dir, "../../PandaBuilds/pandaPIparser")
        pandaPIgrounder_path = os.path.join(script_dir, "../../PandaBuilds/pandaPIgrounder")

        # Output file names based on domain and problem file names
        domain_base = os.path.splitext(os.path.basename(self.domain_file))[0]
        problem_base = os.path.splitext(os.path.basename(self.problem_file))[0]

        if FLAGS.LOG_GROUNDER:
            print(f"Grounding domain: {self.domain_file}\nProblem: {self.problem_file}")

        # Step 1: Parse with pandaPIparser
        parsed_output = "temp.parsed"
        result = subprocess.run(
            [pandaPIparser_path, self.domain_file, self.problem_file, parsed_output],
            check=True
        )
        
        # Check if parsing was successful
        if result.returncode != 0 or not os.path.exists(parsed_output):
            print("Panda Parsing failed.")
            self.grounder_status = 'FAILED'
            return None
        
        if FLAGS.LOG_GROUNDER:
            print("Panda Parsing ended")

        # Step 2: Ground with pandaPIgrounder
        psas_output = f"{domain_base}-{problem_base}.psas"
        result = subprocess.run(
            [pandaPIgrounder_path, "-q", "-D", "-e", parsed_output, psas_output],
            check=True
        )

        os.remove(parsed_output)
        
        # Check if grounding was successful
        if result.returncode != 0 or not os.path.exists(psas_output):
            print("Panda Grounding failed.")
            self.grounder_status = 'FAILED'
            return None
        
        if FLAGS.LOG_GROUNDER:
            print("Panda Grounding completed successfully")
        
        self.grounder_status = 'SUCCESS'
        return psas_output

    def _read_sas_file(self):
        """
        Reads the content of the SAS file.
        """
        with open(self.sas_file, "r") as file:
            return file.read()
    
    def get_model(self):
        """
        Returns the parsed model data from the SAS file.
        Ensure that the parser has been initialized before calling this.
        """
        if not self.sasplus_parser:
            raise RuntimeError("SASPlusParser has not been initialized. Ensure grounding and parsing were successful.")
        return self.sasplus_parser.get_parsed_data()

    def print_model(self):
        """
        Prints the parsed model for verification.
        """
        if self.sasplus_parser:
            self.sasplus_parser.print_parsed_data()
        else:
            print("Model has not been parsed yet.")
