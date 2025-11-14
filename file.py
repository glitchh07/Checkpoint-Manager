import os
import glob     #importing glob to find all specified files
import pickle   #importing pickle to handle muliple file formats
import shutil
import time

class CheckpointManager:

    def __init__(self, save_dir :str=os.getcwd(), filenames_dict :dict=None) ->None:
        
        self.start_time = time.time()   #getting the startime
        self.save_dir = save_dir #getting the save dir
        
        #these are for simple auto backups
        self.auto_backup_dict = {}  #dict for containing all the auto backup paths with filename as key
        self.last_backup_time = {}
        self.auto_backup_success = {}

        #these are for smart auto backup fuction
        self.last_progress = {}
        self.smart_last_backup_time = {}
        self.smart_backup_dict = {} #dict for containing all smart backup paths with filename as their key
        self.smart_backup_count={}

        #these are for normal checkpoints
        self.filenames = [] #defining var(S) for each filename
        self.config = {}
        self.path = {}
        # self.data = {}
        
        if filenames_dict: #assining values to these var(S) if given
            self.filenames = filenames_dict.keys()
            for f in self.filenames: 
                self.config[f] = filenames_dict[f]
                self.path[f] = os.path.join(save_dir, f)
    
        
        os.makedirs(self.save_dir, exist_ok=True)    #creating folder if doesnt exist

    #all of non self depended functions here
    @staticmethod
    def _save_specific_file(dir :str, name :str, data) ->None:
            temp_path = os.path.join(dir, "checkpoint.tmp")    #creating temp path first and checking if it exits then dumping all the data and renaming it
            try:
                with open(temp_path, "wb") as file:
                    pickle.dump(data, file)
                    file.flush()
                    os.fsync(file.fileno())
                final_path = os.path.join(dir, name)
                os.replace(temp_path, final_path)
                
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print("Removed File!!")
                print(f"Saving failed: {e}")
            
    @staticmethod
    def _copy_specific_file(path1 :str, path2 :str, config :any=None) ->bool:
        if path1 and path2 and os.path.exists(path1):   #checking if main and file exists
            try:
                with open(path1, "rb") as main: #checking config from main file
                    if config:  #checking if config is given and if it doesnt match retuning false
                        data = pickle.load(main)
                        if not data: print("File is empty!! Skipping...") ; return False  #returning if the file is empty
                        if not isinstance(data, dict) or ("metadata" not in data):    #checking if the data is in dict format and has metadata key in it
                            print("\nCopying failed: Invalid checkpoint format...\n")
                            return False
                        if (not data['metadata'].get('config', None)) or data['metadata']['config'] != config: #checking if config matches
                            print("\nCopying failed: Config mismatched...\n")
                            print(f"file config: {data['metadata']['config']}")
                            return False
                    # pickle.dump(data, copy)
                    # copy.flush()
                    # os.fsync(copy.fileno())
                shutil.copy2(path1, path2)  #using shutil to copy
                return True
            except Exception as e:
                print(f"Copying failed: {e}...")
                if os.path.exists(path2): os.remove(path2)
                return False
    
    @staticmethod
    def _load_specific_file(path :str, config :any) ->dict|None: #for loading specific file but mainly used in load files to check for backup files
        try:
            if path and os.path.exists(path):
                if os.path.getsize(path) == 0:
                    print("\n⚠️ Checkpoint file is empty\n")
                    return None
                
                with open(path, "rb") as file:
                    data = pickle.load(file)
                    # Add more validation
                    if not isinstance(data, dict) or "metadata" not in data:    #checking if the data is in dict format and has metadata key in it
                        print("\n⚠️ Invalid checkpoint format\n")
                        return None

                    if data["metadata"]["config"] != config:    #checking if the entered config matches with the data
                        print("\n⚠️ Checkpoint config mismatch — skipping file...\n")
                        print(f"file config: {data['metadata']['config']}")
                        return None                   
                    else:   #returning data if the config matches                  
                        # print(f"\n☑️Resuming after {elapsed:.2f} seconds of previous run.\n")
                        return data
            else: 
                return None     #if the file doesnt exist
            
        except Exception as e:   #showing error if there is an error
            print(f"\n⚠️ Corrupted checkpoint: {e}\n")
            return None
        
    @staticmethod
    def _remove_specific_file(path :str, config :any) ->bool:
        try:
            if path and os.path.exists(path):
                if config:
                    with open(path, "rb") as f:
                        data = pickle.load(f)
                        if not isinstance(data, dict) or ("metadata" not in data):    #checking if the data is in dict format and has metadata key in it
                            print("\nCopying failed: Invalid checkpoint format...\n")
                            return False
                        if (not data['metadata'].get('config', None)) or data['metadata']['config'] != config: #checking if config matches
                            print("\nCopying failed: Config mismatched...\n")
                            print(f"file config: {data['metadata']['config']}")
                            return False
                os.remove(path)
                return True
        except Exception as e:
            print(f"Removing failed: {e}")
            return False
        
    @staticmethod
    def _verify_save(path: str) ->bool:    #function for verifying after saving
        if not path:    #returning False if no path entered
            print("No path entered!! Skipping...")
            return False
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            return isinstance(data, dict)
        except Exception as e:
            print(f"⚠️ Checkpoint verification failed: {e}")
            return False

    #all of self depended function starts from here
    def save_file(self, data :dict, filename_dict :dict=None, progress=None):
        if not filename_dict: 
            print("No data entered!! skipping saving...")
            return    #will skip if no file registered
  
        if not isinstance(data, dict):
            raise ValueError("Data should be a 'dict'")

        # filename = list(filename_dict.keys())
        # config = list(filename_dict.values())

        for filename, config in filename_dict.items():
            if filename not in self.filenames:
                self.filenames.append(filename)
                self.path[filename] = os.path.join(self.save_dir, filename)
                self.config[filename] = config
                print("\nNew filename registered!!\n")
            
            for attempt in range(3):    #for loop if cant read file each time after saving for 3 times
                
                #updating the data before saving
                metadata = {}
                metadata["timestamp"] = time.ctime()
                metadata['elapsed'] = time.time() - self.start_time
                metadata['config'] = config
                # self.data.setdefault(filename, {})
                # self.data[filename]= data
                full_data = {"metadata": metadata, "data": data}

                self._save_specific_file(self.save_dir, filename, full_data)  #calling the function for saving

                if self._verify_save(self.path[filename]): #verifying the saved file after each save

                    if not progress:
                        print("\n✅ Checkpoint verified and saved.\n")
                    else:
                        if progress >= 100_000_000_000:
                            if progress % 100_000_000_000 == 0:
                                print(f"\n✅ Checkpoint verified and saved {progress} times!!\n")
                        if progress >= 100_000_000:
                            if progress % 100_000_000 == 0:
                                print(f"\n✅ Checkpoint verified and saved {progress} times!!\n")
                        elif progress >= 1_000_000:
                            if progress % 1_000_000 == 0:
                                print(f"\n✅ Checkpoint verified and saved {progress} times!!\n")
                        elif progress >= 1000:
                            if progress % 1000 == 0:
                                print(f"\n✅ Checkpoint verified and saved {progress} times!!\n")
                        elif progress >= 10:
                            if progress % 10 == 0:
                                print(f"\n✅ Checkpoint verified and saved {progress} times!!\n")
                        else:
                            print("\n✅ Checkpoint verified and saved.\n")

                    break
                else:
                    print(f"\n⚠️ Attempt {attempt+1} failed, retrying...\n")
            else:
                print("\n❌ Failed to save after 3 attempts.\n")
    
    def load_files(self, filenames_dict :dict=None) ->dict|None:  #main loading file fuction
        
        # filenames = list(filenames_dict.keys())
        # config = list(filenames_dict.values())
        
        if not filenames_dict: filenames_dict=self.config #getting the self all filenames if its not entered
        if not filenames_dict:
            print("No file found!! Skipping loading...")
            return None

        for filename, config in filenames_dict.items():   #getting filenames and config from the dict
            print(f"\nTrying loading up total {len(filenames_dict.items())} files...\n")

            final_data = None   #defining the final path var
            if not config: config=self.config.setdefault(filename, None)    #getting config from self (if config not entered)  if the filename is registered

            #searching for main checkpoints with the same name and loading the recent one if config matched after sorting
            main_path = glob.glob(os.path.join(self.save_dir, f"{filename}"))
            more_path = glob.glob(os.path.join(self.save_dir, f"*@@@{filename}"))    #finding more checkpoints and extending if found any
            if more_path: main_path.extend(more_path) 
            main_path.sort(key=os.path.getctime, reverse=True)   #sorting by creation time
            for path in main_path:
                data = self._load_specific_file(path, config)  #trying main file first
                if data: break
            else: data = None

            if data:
                ask = input("📁Existing checkpoint found!! Load (y/n)? ").strip().lower()
                if ask not in ("n", "no", "N"):
                    elapsed = data["metadata"].setdefault("elapsed", 0)
                    print(f"\n☑️Resuming after {elapsed:.2f} seconds of previous run.\n")
                    # self.data[filename] = data
                    self.path[filename] = path  #adding the path to self
                    self.config[filename] = data.setdefault('metadata',0).setdefault('config',0)    #updating the config
                    final_data = data['data']   #defining it to a var first instead of returning so that the rest of the function gets triggered even if the data is found
                    break
            
            else: print("\nNo checkpoint file found...")

            #getting all the matched auto backups
            auto_backup_path = glob.glob(os.path.join(self.save_dir, f"auto_backup@@*@@{filename}")) #getting the backup path and extending and sorting it to self backup path
            auto_backup_path.sort(key=lambda x: os.path.basename(x).split("@@")[1], reverse=True) #sorting the list
            
            if auto_backup_path and self._verify_save(auto_backup_path[0]): self.auto_backup_success[filename]= True    #setting last backup success to True if verified

            if auto_backup_path:    #checking if there is a chekpoint file available
                for f in auto_backup_path:
                    data = self._load_specific_file(f, config)
                    if data:
                        ask = input("\n📁Existing backup file found!! Load (y/n)? ").strip().lower()
                        if ask not in ("no", "n", "N"):
                            # self.data[filename] = data
                            self.config[filename] = data.setdefault('metadata',0).setdefault('config',0)
                            self.auto_backup_dict.setdefault(filename, []).append(auto_backup_path)  #updating the dict value
                            if not final_data: final_data = data['data']  #if no data found yet loading from auto backup
                            break
            else: print("No auto backups files found...")
            
            #getting all the matched smart backups
            smart_backup_path = glob.glob(os.path.join(self.save_dir, f"smartbackup*{filename}"))  #getting all the files matching the filename and sorting after adding them into a list and adding them to self smart backup dict
            smart_backup_path.sort(key=lambda x : os.path.basename(x).split('@@')[1], reverse=True)

            if smart_backup_path:    #checking if any files found
                print(f"📁Found {len(smart_backup_path)} smart backups.")
                
                # Show newest 3
                for i, backup in enumerate(smart_backup_path):
                    print(f"  {i+1}. {os.path.basename(backup)}")
                    self.smart_backup_count.setdefault(filename, 0)
                    self.smart_backup_count[filename] += 1
                
                if input("Load latest? (y/n): ").lower() in ("y", "yes", ""):
                    # Try backups in order until one works
                    for backup in smart_backup_path:
                        data = self._load_specific_file(backup, config)
                        if data:
                            print(f"✅ Loaded: {os.path.basename(backup)}")
                            # self.data[filename] = data
                            self.config[filename] = data.setdefault('metadata',0).setdefault('config',0)
                            self.smart_backup_dict.setdefault(filename, []).append(smart_backup_path)   #updating the dict value
                            if not final_data : final_data = data['data'] #if no data found it loading from smart backup
                            break
            else: print("No smart backups found...\n")
        
        return final_data if final_data else None #returning the loaded data if found else None
        
    def auto_backup(self, interval=60, modify=True, filenames_dict: list|str|dict=None) ->None:   #for single auto backups of same name
        
        if not filenames_dict: filenames_dict=self.config #getting the config with filename keys if filenames not given
        if not filenames_dict:   #skipping if no file names found even after checking in self filenames
            print("\nNo files found!! Skipping auto backup...\n")
            return

        #sorting out filename and config from filenames and None if config not given
        if isinstance(filenames_dict, dict): items = filenames_dict.items()
        elif isinstance(filenames_dict, (tuple, list)): items = [(f, None) for f in filenames_dict]
        else: items = [(filenames_dict, None)]

        for filename, config in items: 
            print(f"\nBacking up total {len(filenames_dict) if not isinstance(filenames_dict, str) else 1} files...\n")
            if not config: config=self.config.setdefault(filename, 0)  #fetching if config not given

            timestamp = time.strftime("%Y%m%d_%H%M%S")  #getting the time
            name = f"auto_backup@@{timestamp}@@{filename}"    #generating name for the backup
            backup_path = os.path.join(self.save_dir, name)
            auto_backup_dict = self.auto_backup_dict.setdefault(filename, [])
            
            if auto_backup_dict and (filename in [os.path.basename(x).split('@@')[-1] for x in auto_backup_dict]) \
                and modify and self.auto_backup_success.setdefault(filename, False):    #checking if the path already exists and modify is True and the last backup was successful
                files = []
                for f in auto_backup_dict:
                    if os.path.basename(f).split("@@")[-1] == filename:
                        files.append(f)
                files.sort(key=lambda x: os.path.basename(x).split("@@")[1], reverse=True)

                for f in files: #loading the latest matched backup and replacing the path
                    if self._load_specific_file(f, config):                   
                        os.replace(f, backup_path)
                        auto_backup_dict[auto_backup_dict.index(f)] = backup_path
                        break
                else: 
                    print("No auto backups file matched!! creating a new one...")

            #checking if its the first backup or the given interval has passed
            if (not self.last_backup_time.setdefault(filename, 0)) or (time.time() - self.last_backup_time.setdefault(filename, 0) >= interval):  
                
                for attempt in range(3):     #trying 3 times and breaking the loop if backup sucessfull
                    if self.path[filename] and os.path.exists(self.path[filename]):
                        self._copy_specific_file(self.path[filename], backup_path, config=config)    #inserting the function and checking if it was successful
                    
                        if self._verify_save(backup_path):   #verifying the save
                            print("✅ Backup verified and saved.")
                            if backup_path not in auto_backup_dict: #adding to the backup path if its new
                                auto_backup_dict.append(backup_path)
                            auto_backup_dict.sort(key=lambda x: os.path.basename(x).split("@@")[1], reverse=True)
                            self.auto_backup_dict[filename] = auto_backup_dict  #updating the data
                            self.auto_backup_success[filename] = True
                            self.last_backup_time[filename] = time.time()  # reseting time of backup
                            break
                        else:
                            print(f"⚠️ Attempt {attempt+1} failed, retrying...")
        
                else:   #if backup fails
                    print("❌ Failed to create backup after 3 attempts.")
                    self.auto_backup_success[filename] = False
                    # return None
        
 
    def remove_checkpoints(self):   #fuction for removing all checkpoints together


        if self.path.values():   #removing main checkpoint
            for path in self.path.values(): 
                if self._remove_specific_file(path): print("Removed checkpoint!!")


        if self.auto_backup_dict.values():  #removing all auto backups
            for paths in self.auto_backup_dict.values():
                for f in paths:    
                    self._remove_specific_file(f)
        print(f"{len(self.auto_backup_dict.values()) if self.auto_backup_dict.values() else 0} Auto Backup files removed!!")


        if self.smart_backup_dict.values(): #removing all smart backup files
                for n, file in enumerate(self.smart_backup_dict.values(), start=1):
                    self._remove_specific_file(file)
                print(f"{n if 'n' in locals() else 0} Smart Backup files removed!!")
        
    def auto_backup_smart(self, current_progress, min_improvement = 0.1, interval :int|float = 1800, max_backups :int= 5, filenames_dict :list|str|dict=None) ->None:   #smart backup function 

        if not filenames_dict: filenames_dict = self.config
        if not filenames_dict:
            print("No files found!! skipping smart backup...")
            return

        #using for loop for getting filename and config
        if isinstance(filenames_dict, dict): items = filenames_dict.items()
        elif isinstance(filenames_dict, (tuple, list)): items = [(f, None) for f in filenames_dict]
        else: items = [(filenames_dict, None)]

        for filename, config in items:
            if self.smart_last_backup_time.setdefault(filename, 0) and time.time() - self.smart_last_backup_time.setdefault(filename, 0) < interval:  #checking if the given time has passed since last save or this is the first one
                # print("🕒 Smart backup skipped — interval not reached yet.")
                return  None
            
            print(f"\n<smart_backup>: Backing up total {len(filenames_dict)if isinstance(filenames_dict, (list, tuple)) else 1} files...\n")
                
            #saving current progress as the last one if this is the first progress
            if (not self.last_progress.setdefault(filename, 0)) and current_progress:
                self.last_progress[filename] = current_progress
                improvement=1

            else:    #calculating improvement if this is not the first progress
                improvement = ((current_progress - self.last_progress.setdefault(filename, 0)) / self.last_progress.setdefault(filename, 0)) if self.last_progress.setdefault(filename, 0) else 1
    
            if improvement >= min_improvement:  #checking if the condition matches
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_name = f"smartbackup@@{timestamp}@@improved@@{improvement*100:.1f}percent@@{filename}"    #gernarating name for the backup file
                backup_path = os.path.join(self.save_dir, backup_name)
                smart_backup_dict = self.smart_backup_dict.setdefault(filename, [])
                
                for attempt in range(3):
                    if self.path.setdefault(filename, 0) and os.path.exists(self.path[filename]):   #checking if main file exists
                        self._copy_specific_file(self.path[filename], backup_path, config=config)  #inserting the copy function to copy main checkpoint

                        if self._verify_save(backup_path):   
                            print("\n✅ Smart Backup verified and saved.")
                            # self.smart_backup_files.append(backup_path)
                            if not smart_backup_dict:  self.smart_backup_dict[filename] = []     
                            smart_backup_dict.append(backup_path) #appending the new path and sorting
                            smart_backup_dict.sort(key=lambda x: os.path.basename(x).split('@@')[1], reverse=True)
                            self.smart_backup_dict[filename] = smart_backup_dict    #updating the main dict
                            self.last_progress[filename] = current_progress   #updating last progress and last backup time
                            self.smart_last_backup_time[filename] = time.time()
                            self.smart_backup_count.setdefault(filename, 0)
                            self.smart_backup_count[filename] += 1
                                            
                            if smart_backup_dict and (len(smart_backup_dict) > max_backups):  #deleting old backups
                                oldest = self.smart_backup_dict[filename].pop()
                                if os.path.exists(oldest): os.remove(oldest)
                            
                            print(f"🏆 Smart backup #{self.smart_backup_count.setdefault(filename, 0)}: {improvement*100:.1f}% improvement since last backup\n")
                            break

                        else:
                            print(f"⚠️ Attempt {attempt+1} failed, retrying...\n")
                else:
                    print("❌ Failed to save after 3 attempts.\n")
                    try: os.remove(backup_path) #removing the file if verification was unsuccesful
                    except: pass
                    return None
        
    def remove_specific_checkpoints(self, filenames_dict :list|str|dict=None) ->None:   #fuction for removing checkpoints with same config together

        if not filenames_dict: filenames_dict = self.config
        if not filenames_dict: 
            print("No files found!!")  #printing if filename not given
            return

        #using for loop for getting filename and config
        if isinstance(filenames_dict, dict): items = list(filenames_dict.items())
        elif isinstance(filenames_dict, (tuple, list)): items = [(f, None) for f in filenames_dict]
        else: items = [(filenames_dict, None)]

        for filename, config in items:
            print(f"Removing total {len(items)} files...")
            print(f"\nNow trying to remove: {filename}...\n")
            if not config: config=self.config.setdefault(filename, None)
            if self._remove_specific_file(self.path[filename], config): 
                self.path.pop(filename)
                self.config.pop(filename)
                self.filenames.remove(filename)
                print(f"Removed checkpoint: {filename}")
            
            if self.auto_backup_dict.setdefault(filename, []):
                f=0
                for path in self.auto_backup_dict.setdefault(filename, []):
                    if self._remove_specific_file(path, self.config.setdefault(filename, None)):
                        f+=1
                        self.auto_backup_dict.pop(filename, None)
                        self.auto_backup_success.pop(filename, None)
                        self.last_backup_time.pop(filename, None)
                    print(f"Removed total {f} auto backups!!")

            if self.smart_backup_dict.setdefault(filename, []): #removing all smart backup files matching the filename
                f = 0
                for n, file in enumerate(self.smart_backup_dict.setdefault(filename, []), start=1):
                    if self._remove_specific_file(file, config):
                        f+=1
                print(f"{f} Smart Backup files removed!!")
                            
#need to make a way to rename the auto backups after modifying if modify=True   #completed
#need to change the glob filter for smar backups in load_file(). just copy auto backup  #completed
#test smart backups #completed

#change self.backup_path so that it behaves like a dict like the smart one  #completed
#create a _save_specific_fuction()  #completed
#create a _copy_specific_file() function
#make self.config a list and store all the known configs into it and filter out data using the index of these configs   #completed but created as a dict with filename as keys
#debug above 3

#change every variable except filenames to dict that contains filenames as keys #completed

#modify this so that self.path is a dict that contains filename: then all the data data for that filename   #completed but created as a list and everything else is a dict with key as filename
#create a load_all_files() for loading everything and assigning the values to every self var(S) #half-completed dont need it modified load_files to load multiple files and config if entered as an dict and not entered then will load what is available in the self.filenames 

#debug the code #completed

#start from here
#create a _remove_specific_checkpoint like the load specific one then implement it to all the remove functions
#update README.md
#end of version 2.0(changing the core concept so that it works with multiple files)

#version 3.0(adding more functions)
#create the true load all function which just loads every single file in the dir and assigns them to the value automaticaly
#change save function so that it has the modify part like auto_backup and will create multiple checkpoints if modify is False
#change smart backup so that it also has the modify part

#create a save_file_smart like the auto backup smart
#create diff types of auto_backup and save_files 

###make it so that cm works with both defining it multiple times with diff checkpoint names and also with defining/adding multiple checkpoints in a single CM