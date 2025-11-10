import os
import glob     #importing glob to find all specified files
import pickle   #importing pickle to handle muliple file formats
import time

class CheckpointManager:

    def __init__(self, filename, config, save_dir=os.getcwd()):
        
        self.start_time = time.time()   #getting the startime
        self.config = config
        self.save_dir = save_dir #getting the save dir
        self.backup_path = []        #using none for update these in their respective fuction
        self.last_backup_time = None
        self.auto_backup_success = True

        #dict for adding useful infos to the file (for verifying mostly)
        self.metadata = {
            "timestamp": time.ctime(),
            "elapsed": time.time() - self.start_time,
            "config": config
        }

        #these are for smart save fuction
        self.last_progress = 0
        self.smart_last_backup_time = None
        # self.smart_backup_files = glob.glob(os.path.join(self.save_dir, "smartbackup*"))
        self.smart_backup_dict = {}
        self.smart_backup_count=0

        self.filename = filename
        self.path = os.path.join(self.save_dir, filename)    #creating path to save file and loading it if it exists
        self.data = None
        
        os.makedirs(self.save_dir, exist_ok=True)    #creating folder if doesnt exist

    def save_file(self, data, progress=None):
  
        if not isinstance(data, dict):
            raise ValueError("Data should be a 'dict'")
        
        for attempt in range(3):    #for loop if cant read file each time after saving for 3 times
            
            #updating the data before saving
            self.metadata["timestamp"] = time.ctime()
            self.metadata['elapsed'] = time.time() - self.start_time
            self.data = data
            self.full_data = {"metadata": self.metadata, "data": self.data}

            temp_path = os.path.join(self.save_dir, "checkpoint.tmp")    #creating temp path first and checking if it exits then dumping all the data and renaming it
            with open(temp_path, "wb") as file:
                pickle.dump(self.full_data, file)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_path, self.path)

            if self.verify_save(self.path): #verifying the saved file after each save
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

    
    @staticmethod
    def _load_specific_file(path, config): #for loading specific file but mainly used in load files to check for backup files
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
                        print("\n⚠️ Checkpoint config mismatch — skipping resume.\n")
                        print(f"file config: {data['metadata']['config']}")
                        return None                   
                    else:   #showing elapsed time
                        elapsed = data["metadata"].get("elapsed", 0)
                        print(f"\n☑️Resuming after {elapsed:.2f} seconds of previous run.\n")
                        return data["data"]
            else: 
                return None     #if the file doesnt exist
            
        
        except (pickle.PickleError, EOFError, KeyError) as e:   #showing error if there is an error
            print(f"\n⚠️ Corrupted checkpoint: {e}\n")
            return None

    def load_file(self, config=None, filename :str=None):    #main loading file fuction
        
        if not config: config=self.config   #getting the config if its not entered
        if not filename: filename=self.filename #getting the self filename if its not entered

        data = self._load_specific_file(self.path, config)  #trying main file first
        if data:
            ask = input("📁Existing checkpoint found!! Load (y/n)? ").strip().lower()
            if ask not in ("n", "no", "N"):
                self.data = data
                return data
        
        print("\nNo checkpoint file found...")
        backup_path = glob.glob(os.path.join(self.save_dir, f"auto_backup@@*@@{filename}")) #getting the backup path and extending and sorting it to self backup path
        self.backup_path.extend(backup_path)
        # print(self.backup_path)
        self.backup_path.sort(key=lambda x: os.path.basename(x).split("@@")[1], reverse=True)

        if self.backup_path:    #checking if there is a chekpoint file available
            for f in self.backup_path:
                data = self._load_specific_file(f,config)
                if data:
                    ask = input("\n📁Existing backup file found!! Load (y/n)? ").strip().lower()
                    if ask not in ("no", "n", "N"):
                        self.data = data
                        return data
        else: print("No auto backups files found!!")
        
        smart_backup_path = glob.glob(os.path.join(self.save_dir, f"smartbackup*{filename}"))  #getting all the files matching the filename and sorting after adding them into a list and adding them to self smart backup dict
        smart_backup_path.sort(key=lambda x : os.path.basename(x).split('@@')[1], reverse=True)
        if smart_backup_path: self.smart_backup_dict[filename] = smart_backup_path

        if self.smart_backup_dict.get(filename, []):
            print(f"📁Found {len(self.smart_backup_dict.get(filename, []))} smart backups.")
            
            # Show newest 3
            for i, backup in enumerate(self.smart_backup_dict.get(filename, [])):
                print(f"  {i+1}. {os.path.basename(backup)}")
                self.smart_backup_count+=1
            
            if input("Load latest? (y/n): ").lower() in ("y", "yes", ""):
                # Try backups in order until one works
                for backup in self.smart_backup_dict.get(filename, []):
                    data = self._load_specific_file(backup, config)
                    if data:
                        print(f"✅ Loaded: {os.path.basename(backup)}")
                        self.data = data
                        return data
        
    def auto_backup(self, interval=60, modify=True, filename: str=None, config=None):   #for single auto backups of same name
        
        if not config: config=self.config   #assigning the var(S) to self values if not defined
        if not filename: filename=self.filename

        timestamp = time.strftime("%Y%m%d_%H%M%S")  #getting the time
        name = f"auto_backup@@{timestamp}@@{filename}"    #generating name for the backup
        backup_path = os.path.join(self.save_dir, name)
        
        if self.backup_path and (filename in [os.path.basename(x).split('@@')[-1] for x in self.backup_path]) and modify and self.auto_backup_success:    #checking if the path already exists and modify is True
            files = []
            for f in self.backup_path:
                if os.path.basename(f).split("@@")[-1] == filename:
                    files.append(f)
            files.sort(key=lambda x: os.path.basename(x).split("@@")[1], reverse=True)

            for f in files: #loading the latest matched backup and replacing the path
                if self._load_full_file(f, config):                   
                    os.replace(f, backup_path)
                    self.backup_path[self.backup_path.index(f)] = backup_path
                    break
            else: 
                print("No auto backups file matched!! creating a new one...")

        if (not self.last_backup_time) or (time.time() - self.last_backup_time >= interval):  
            try:
                for attempt in range(3):     #trying 3 times and breaking the loop if backup sucessfull
                    if self.path and os.path.exists(self.path):
                        with open(self.path, "rb") as main, open(backup_path, "wb") as backup:  #opening the main file and copying everything
                            backup.write(main.read())
                            backup.flush()
                            os.fsync(backup.fileno())
                            # pickle.dump(pickle.load(main), backup)
                        print("💾 Backup created!")
                    self.last_backup_time = time.time()  # reseting time of backup
                    
                    if self.verify_save(backup_path):   #verifying the save
                        print("✅ Backup verified and saved.")
                        if backup_path not in self.backup_path: #adding to the backup path if its new
                            self.backup_path.append(backup_path)
                        self.backup_path.sort(key=lambda x: os.path.basename(x).split("@@")[1], reverse=True)
                        self.auto_backup_success = True
                        break
                    else:
                        print(f"⚠️ Attempt {attempt+1} failed, retrying...")
        
                else:
                    print("❌ Failed to create backup after 3 attempts.")
                    self.auto_backup_success = False
                    # return None
        
            except (pickle.PickleError, EOFError, KeyError) as e:   #showing error if there is an error
                print(f"⚠️ Corrupted checkpoint: {e}")
                self.auto_backup_success = False
                # return None
 
    def remove_checkpoints(self):   #fuction for removing all checkpoints together

        try:
            if self.path and os.path.exists(self.path):   #removing main checkpoint
                os.remove(self.path)
                print("Removed checkpoint!!")
        except FileNotFoundError:
            pass

        try:
            if self.backup_path:
                for f in self.backup_path:
                    if os.path.exists(f):    #checking for simple backup files
                        os.remove(f)
                print("Removed all auto backup checkpoints!!")
        except FileNotFoundError:
            pass

        if self.smart_backup_dict.values(): #removing all smart backup files
                for n, file in enumerate(self.smart_backup_dict.values(), start=1):
                    try:
                        os.remove(file)
                    except FileNotFoundError:
                        pass
                print(f"{n if 'n' in locals() else 0} Smart Backup files removed!!")

    def verify_save(self, path):    #function for verifying after saving
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            return isinstance(data, dict)
        except Exception as e:
            print(f"⚠️ Checkpoint verification failed: {e}")
            return False
        
    def auto_backup_smart(self, current_progress, min_improvement = 0.1, interval = 1800, max_backups = 5, filename=None):   #smart backup function 

        if not filename: filename = self.filename

        try:
            if self.smart_last_backup_time and time.time() - self.smart_last_backup_time < interval:  #checking if the given time has passed since last save or this is the first one
                # print("🕒 Smart backup skipped — interval not reached yet.")
                return  None
                
            #saving current progress as the last one if this is the first progress
            if (not self.last_progress) and current_progress:
                self.last_progress = current_progress
                improvement=1

            else:    #calculating improvement if this is not the first progress
                improvement = ((current_progress - self.last_progress) / self.last_progress) if self.last_progress else 1
    
            if improvement >= min_improvement:  #checking if the condition matches
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_name = f"smartbackup@@{timestamp}@@improved@@{improvement*100:.1f}percent@@{filename}"    #gernarating name for the backup file
                backup_path = os.path.join(self.save_dir, backup_name)
                
                for attempt in range(3):
                    if self.path and os.path.exists(self.path):   #checking if main file exists
                        with open(self.path, "rb") as main, open(backup_path, "wb") as backup:  #copying data from main file
                            backup.write(main.read())
                            backup.flush()
                            os.fsync(backup.fileno())
                        
                        if self.verify_save(backup_path):   
                            print("\n✅ Smart Backup verified and saved.")
                            # self.smart_backup_files.append(backup_path)
                            if not self.smart_backup_dict.get(filename, []):  self.smart_backup_dict[filename] = []     
                            self.smart_backup_dict.setdefault(filename, []).append(backup_path)
                            self.smart_backup_dict[filename].sort(key=lambda x: os.path.basename(x).split('@@')[1], reverse=True)
                            self.last_progress = current_progress   #updating last progress and last backup time
                            self.smart_last_backup_time = time.time()
                            self.smart_backup_count+=1
                                            
                            if self.smart_backup_dict.get(filename, []) and (len(self.smart_backup_dict.get(filename, [])) > max_backups):  #deleting old backups
                                oldest = self.smart_backup_dict[filename].pop()
                                if os.path.exists(oldest): os.remove(oldest)
                            
                            print(f"🏆 Smart backup #{self.smart_backup_count}: {improvement*100:.1f}% improvement\n")
                            break

                        else:
                            print(f"⚠️ Attempt {attempt+1} failed, retrying...\n")
                else:
                    print("❌ Failed to save after 3 attempts.\n")
                    return None
            
        except (IOError, OSError) as e:
            print(f"❌ Smart backup failed: {e}\n")
            return None
        
    @staticmethod
    def _load_full_file(path, config): #for loading full file including metadata and config but mainly used in remove specific checkpoints
        try:
            if os.path.exists(path):
                if os.path.getsize(path) == 0:
                    # print("⚠️ Checkpoint file is empty")
                    return None
                
                with open(path, "rb") as file:
                    data = pickle.load(file)
                    # Add more validation
                    if not isinstance(data, dict) or "metadata" not in data:    #checking if the data is in dict format and has metadata key in it
                        # print("⚠️ Invalid checkpoint format")
                        return None

                    if data["metadata"]["config"] != config:    #checking if the entered config matches with the data
                        # print("⚠️ Checkpoint config mismatch — skipping resume.")
                        # print(f"file config: {data['metadata']['config']}")
                        return None                   
                    else:   #showing elapsed time
                        # elapsed = data["metadata"].get("elapsed", 0)
                        # print(f"☑️Resuming after {elapsed:.2f} seconds of previous run.")
                        return data
            else: 
                return None     #if the file doesnt exist
            
        
        except (pickle.PickleError, EOFError, KeyError) as e:   #showing error if there is an error
            # print(f"⚠️ Corrupted checkpoint: {e}")
            return None
        
    def remove_specific_checkpoints(self, config=None, filename=None):   #fuction for removing checkpoints with same config together

        if not config: config=self.config   #getting the filename and config from self if not given
        if not filename: filename=self.filename

        try:
            if self.path and os.path.exists(self.path):   #removing main checkpoint
                data = self._load_full_file(self.path, config)
                if data and data['metadata'].get('config') == config:
                    os.remove(self.path)
                    print("Removed checkpoint!!")
                else:
                    pass
        except (FileNotFoundError, ValueError):
            pass
        
        try:
            if self.backup_path:
                for path in self.backup_path:
                    if os.path.exists(path):
                        data = self._load_full_file(path, config)
                        if data and data['metadata'].get('config') == config:
                            os.remove(path)
                            print(f"Removed backup checkpoint: {os.path.basename(path)}")

        except (FileNotFoundError, ValueError):
            pass

        if self.smart_backup_dict.get(filename, []): #removing all smart backup files matching the filename
                f = 0
                for n, file in enumerate(self.smart_backup_dict.get(filename, []), start=1):
                    try:
                        data = self._load_full_file(file, config)
                        if data and data['metadata'].get('config', 0) == config:
                            os.remove(file)
                            f+=1
                        else:
                            pass
                    except (FileNotFoundError, ValueError):
                        pass
                print(f"{f} Smart Backup files removed!!")
                        
#need to make a way to rename the auto backups after modifying if modify=True   #completed
#need to change the glob filter for smar backups in load_file(). just copy auto backup  #completed
#test smart backups #completed

#change self.backup_path so that it behaves like a dict like the smart one
#create a _save_specific_fuction()
#make self.config a list and store all the known configs into it and filter out data using the index of these configs

#modify this so that self.path is a dict that contains filename: then all the data data for that filename
#create a load_all for loading everything and assigning the values to every self var(S)
#create a _remove_specific_checkpoint like the load specific one then implement it to all the remove functions

###make it so that cm works with both defining it multiple times with diff checkpoint names and also with defining/adding multiple checkpoints in a single CM