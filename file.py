import os
import glob     #importing glob to find all specified files
import pickle   #importing pickle to handle muliple file formats
import time

class CheckpointManager:

    def __init__(self, filename, config, save_dir=None):
        
        self.save_dir = save_dir or os.getcwd()
        self.path = os.path.join(self.save_dir, filename)    #creating path to save file and loading it if it exists
        self.data = self.load_file(config)
        self.start_time = time.time()   #getting the startime
        self.backup_path = None         #using none for update these in their respective fuction
        self.last_backup_time = None
        #dict for adding useful infos to the file for verifying mostly
        self.metadata = {
            "timestamp": time.ctime(),
            "elapsed": time.time() - self.start_time,
            "config": config
        }

        #these are for smart save fuction
        self.last_progress = None
        self.smart_backup_count = 0
        self.smart_last_backup_time = None
        self.smart_backup_files = glob.glob(os.path.join(self.save_dir, "smartbackup*"))
        
        os.makedirs(self.save_dir, exist_ok=True)    #creating folder if doesnt exist


    def save_file(self, data):
  
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
                print("✅ Checkpoint verified and saved.")
                break
            else:
                print(f"⚠️ Attempt {attempt+1} failed, retrying...")
        else:
            print("❌ Failed to save after 3 attempts.")

    
    @staticmethod
    def _load_specific_file(path, config): #for loading specific file but mainly used in load files to check for backup files
        try:
            if os.path.exists(path):
                if os.path.getsize(path) == 0:
                    print("⚠️ Checkpoint file is empty")
                    return None
                
                with open(path, "rb") as file:
                    data = pickle.load(file)
                    # Add more validation
                    if not isinstance(data, dict) or "metadata" not in data:    #checking if the data is in dict format and has metadata key in it
                        print("⚠️ Invalid checkpoint format")
                        return None

                    if data["metadata"]["config"] != config:    #checking if the entered config matches with the data
                        print("⚠️ Checkpoint config mismatch — skipping resume.")
                        print(f"file config: {data['metadata']['config']}")
                        return None                   
                    else:   #showing elapsed time
                        elapsed = data["metadata"].get("elapsed", 0)
                        print(f"☑️Resuming after {elapsed:.2f} seconds of previous run.")
                        return data["data"]
            else: 
                return None     #if the file doesnt exist
            
        
        except (pickle.PickleError, EOFError, KeyError) as e:   #showing error if there is an error
            print(f"⚠️ Corrupted checkpoint: {e}")
            return None

    def load_file(self, config):    #main loading file fuction
        
        data = self._load_specific_file(self.path, config)  #trying main file first
        if data:
            ask = input("📁Existing checkpoint found!! Load (y/n)?").strip().lower()
            if ask not in ("n", "no", "N"):
                return data
        
        print("\nNo checkpoint file found...")
        if self.backup_path:    #checking if there is a chekpoint file available
            ask = input("\n📁Existing backup file found!! Load (y/n)?").strip().lower()
            if ask not in ("no", "n", "N"):
                return  self._load_specific_file(self.backup_path, config)
        
        if self.smart_backup_files:
            print(f"📁Found {len(self.smart_backup_files)} smart backups")
            
            # Show newest 3
            for i, backup in enumerate(self.smart_backup_files[:3]):
                print(f"  {i+1}. {os.path.basename(backup)}")
            
            if input("Load latest? (y/n): ").lower() in ("y", "yes", ""):
                # Try backups in order until one works
                for backup in self.smart_backup_files:
                    data = self._load_specific_file(backup, config)
                    if data:
                        print(f"✅ Loaded: {os.path.basename(backup)}")
                        return data

        
    def auto_backup(self, backup_name, interval):   #for single auto backups
        if not self.backup_path:
            self.backup_path = os.path.join(self.save_dir, backup_name)
        if (not self.last_backup_time) or (time.time() - self.last_backup_time >= interval):
            if os.path.exists(self.path):
                with open(self.path, "rb") as main, open(self.backup_path, "wb") as backup:
                    backup.write(main.read())
                    backup.flush()
                    os.fsync(backup.fileno())
                    # pickle.dump(pickle.load(main), backup)
                print("💾 Backup created!")
            self.last_backup_time = time.time()  # reseting timer

 
    def remove_checkpoints(self):   #fuction for removing all checkpoints together

        try:
            if os.path.exists(self.path):   #removing main checkpoint
                os.remove(self.path)
                print("Removed checkpoint!!")
        except FileNotFoundError:
            pass

        try:
            if os.path.exists(self.backup_path):    #checking for simple backup files
                os.remove(self.backup_path)
                print("Removed backup checkpoint!!")
        except FileNotFoundError:
            pass

        if self.smart_backup_files: #removing all smart backup files
                for n, file in enumerate(self.smart_backup_files, start=1):
                    try:
                        os.remove(file)
                    except FileNotFoundError:
                        pass
                print(f"{n if 'n' in locals() else 0} Smart Backup files removed!!")

    def verify_save(self, path):    #function for verifying after saving
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            if not isinstance(data, dict):
                return False
            return True
        except Exception as e:
            print(f"⚠️ Checkpoint verification failed: {e}")
            return False
        
    def auto_backup_smart(self, batch, min_improvement = 0.1, interval = 1800, max_backups = 5):   #smart backup function 

        try:
            if self.smart_last_backup_time and time.time() - self.smart_last_backup_time < interval:  #checking if the given time has passed since last save or this is the first one
                return False
            
            current_progress = batch   #saving current progress as the last one if this is the first
            if not self.last_progress and current_progress:
                self.last_progress = current_progress

            #calculating improvement
            improvement = (current_progress - self.last_progress)/self.last_progress  if self.last_progress and self.last_progress != 0 else improvement = 1
                
            if improvement >= min_improvement:  #checking if the condition matches
                self.smart_backup_count += 1
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_name = f"smartbackup_{timestamp}_improved_{improvement*100:.1f}percent.pkl"    #gernarating name for the backup file
                backup_path = os.path.join(self.save_dir, backup_name)
                self.smart_backup_files.append(backup_path)
                self.smart_backup_files.sort(key=lambda x: os.path.basename(x).split('_')[1], reverse=True)
                
                if len(self.smart_backup_files) > max_backups and self.smart_backup_files:  #deleting old backups
                    oldest = self.smart_backup_files.pop()
                    os.remove(oldest)
                else:
                    pass
                
                if os.path.exists(self.path):   #checking if main file exists
                    with open(self.path, "rb") as main, open(backup_path, "wb") as backup:  #copying data from main file
                        backup.write(main.read())
                        backup.flush()
                        os.fsync(backup.fileno())
                    
                    self.last_progress = current_progress   #updating last progress and last backup time
                    self.smart_last_backup_time = time.time()
                    
                    print(f"🏆 Smart backup #{self.smart_backup_count}: {improvement*100:.1f}% improvement")
                    return True
            
        except (IOError, OSError) as e:
            print(f"❌ Smart backup failed: {e}")
            return False
        
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
        
    def remove_specific_checkpoints(self, config):   #fuction for removing checkpoints with same config together

        try:
            if os.path.exists(self.path):   #removing main checkpoint
                data = self._load_full_file(self.path, config)
                if data and data['metadata'].get('config') == config:
                    os.remove(self.path)
                    print("Removed checkpoint!!")
                else:
                    pass
        except FileNotFoundError:
            pass
        
        try:
            if os.path.exists(self.backup_path):    #checking for simple backup files
                data = self._load_full_file(self.backup_path, config)
                if data and data['metadata'].get('config', None) == config:
                    os.remove(self.backup_path)
                    print("Removed backup checkpoint!!")
                else:
                    pass
        except FileNotFoundError:
            pass

        if self.smart_backup_files: #removing all smart backup files
                f = 0
                for n, file in enumerate(self.smart_backup_files, start=1):
                    try:
                        data = self._load_full_file(file, config)
                        if data and data['metadata'].get('config', 0) == config:
                            os.remove(file)
                            f+=1
                        else:
                            pass
                    except FileNotFoundError:
                        pass
                print(f"{f} Smart Backup files removed!!")
                        
