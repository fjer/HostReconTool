import wmi, sqlite3, sys, math, netaddr, socket

class WMIConnection:
	
	def __init__(self, remote, verbose, lock, database, stout):
		self.remote = remote
		self.w = None
		self.verbose = verbose
		self.lock = lock
		self.database = database
		self.stout = stout
		#if a remote IP has been provided, set ipAddr to that IP
		if remote != "":
			self.ipAddr = str(remote)
		#else set it to the local system's IP
		else:
			self.ipAddr = socket.gethostbyname(socket.gethostname())
		
	#make a WMI connection with a non-standard namespace
	def connect(self, namespace):
		if self.remote != "":
			self.w = wmi.WMI(self.remote, namespace=mNamespace)
		else:
			self.w = wmi.WMI(namespace=mNamespace)

	#make a WMI connection with the standard namespace
	def connect(self):
		if self.remote != "":
			self.w = wmi.WMI(self.remote)
		else:
			self.w = wmi.WMI()
		
	#connect the DB cursor
	def connectDB(self, cursor):
		self.c = cursor
	
	#use eval to access each attribute under a try/except paradigm	
	def check(self, obj, attrib):
		try:
			return str(eval("obj." + attrib))
		except UnicodeEncodeError:
			return (eval("obj." + attrib)).encode('utf-8')
		except AttributeError:
			return "NO RESULT"
			
	def all_system(self):
		self.sysinfo()
		self.patches()
		self.timezone()
		self.bios()
		self.os()
		self.vss()
		
	def all_user(self):
		self.users()
		self.netlogin()
		self.profiles()
		self.groups()
		
	def all_hardware(self):
		self.pdisks()
		self.ldisks()
		self.memory()
		self.processors()
		self.pnp()
		
	def all_software(self):
		self.startup()
		self.drivers()
		self.process()
		self.services()
		self.products()
		
	def all_network(self):
		self.adapters()		
		self.shares()
		
	def all(self):
		self.all_system()
		self.all_user()
		self.all_hardware()
		self.all_software()
		self.all_network()
		
	#enter data from wmi query into db
	def dbEntry(self, itemList, uniqueList, name, dataList):
		db = sqlite3.connect(self.database)
		db.text_factory = str
		c = db.cursor()
		self.lock.acquire()
		try:
			#create table
			c.execute('''CREATE TABLE ''' + name + ''' (ipAddr text,''' + (''' {} text,''' * len(itemList)).format(*itemList) +  '''unique (''' + uniqueList + '''))''')
		except sqlite3.OperationalError:
			pass
		#for each object in the data list
		for data in dataList:
			try:
				#initial value for all table entries
				values = [self.ipAddr]
				#for each potential element of the object, add it to the values list
				for item in itemList:
					values.append(self.check(data, item.replace("__","")))
				#enter the values into the db
				c.execute('INSERT INTO ' + name + ' VALUES (?' + ', ?' * (len(values) - 1) + ')', values)
			except sqlite3.IntegrityError:
				pass
		db.commit()
		db.close()
		self.lock.release()
		
		
	def wmiQuery(self, title, wmiString, itemList, uniqueList, tableName):
		if (self.verbose): print("Fetching %s data from %s" % (title, self.ipAddr))
		try:
			wmiObject = eval(wmiString)
			if self.database != "": self.dbEntry(itemList, uniqueList, tableName, wmiObject)
			if self.stout:
				for item in wmiObject:
					print(item)
			return
		except AttributeError:
			if (self.verbose): print("Failed to fetch %s data" % (title))
			return

	#comments on this method apply to the other WMI methods
	def sysinfo(self):
		#list of every element of the wmi object
		itemList = ("ComputerName", "AdminPasswordStatus", "AutomaticManagedPagefile", "AutomaticResetBootOption", "AutomaticResetCapability", "BootROMSupported", "BootStatus", "BootupState", "Caption", "ChassisBootupState", "ChassisSKUNumber", "CreationClassName", "CurrentTimeZone", "Description", "DNSHostName", "Domain", "DomainRole", "EnableDaylightSavingsTime", "FrontPanelResetStatus", "HypervisorPresent", "InfraredSupported", "KeyboardPasswordStatus", "Manufacturer", "Model", "NetworkServerModeEnabled", "NumberOfLogicalProcessors", "NumberOfProcessors", "OEMArray", "PartOfDomain", "PauseAfterReset", "PCSystemType", "PCSystemTypeEx", "PowerOnPasswordStatus", "PowerState", "PowerSupplyState", "PrimaryOwnerName", "ResetCapability", "ResetCount", "ResetLimit", "Roles", "Status", "SystemFamily", "SystemSKUNumber", "SystemType", "ThermalState", "TotalPhysicalMemory", "UserName", "WakeUpType", "Workgroup")			
		#unique values for the db
		uniqueList = "ipAddr"
		#call function to process the WMI query
		self.wmiQuery("system", "self.w.Win32_ComputerSystem()", itemList, uniqueList, "sys_data")
		return
		
	def users(self):
		itemList = ("AccountType", "Caption", "Description", "Disabled", "Domain", "FullName", "LocalAccount", "Lockout", "Name", "PasswordChangeable", "PasswordExpires", "PasswordRequired", "SID", "SIDType", "Status")
		uniqueList = "ipAddr, SID"
		self.wmiQuery("Users", "self.w.Win32_UserAccount()", itemList, uniqueList, "user_data")
		return

	def netlogin(self):
		itemList = ("Caption", "Description", "SettingID", "AccountExpires", "AuthorizationFlags", "BadPasswordCount", "CodePage", "Comment", "CountryCode", "Flags", "FullName", "HomeDirectory", "HomeDirectoryDrive", "LastLogoff", "LastLogon", "LogonHours", "LogonServer", "MaximumStorage", "Name", "NumberOfLogons", "Parameters", "PasswordAge", "PasswordExpires", "PrimaryGroupId", "Privileges", "Profile", "ScriptPath", "UnitsPerWeek", "UserComment", "UserId", "UserType", "Workstations")
		uniqueList = "ipAddr, Caption"
		self.wmiQuery("net logon", "self.w.Win32_NetworkLoginProfile()", itemList, uniqueList, "net_login")
		return
				
	def groups(self):
		itemList = ("Caption", "Description", "Domain", "LocalAccount", "Name", "SID", "SIDType", "Status")
		uniqueList = "ipAddr, SID"
		self.wmiQuery("group", "self.w.Win32_Group()", itemList, uniqueList, "group_data")
		return

	def ldisks(self):		
		itemList = ("Access", "Availability", "BlockSize", "Caption", "Compressed", "ConfigManagerErrorCode", "ConfigManagerUserConfig", "CreationClassName", "Description", "DeviceID", "DriveType", "ErrorCleared", "ErrorDescription", "ErrorMethodology", "FileSystem", "FreeSpace", "InstallDate", "LastErrorCode", "MaximumComponentLength", "MediaType", "Name", "NumberOfBlocks", "PNPDeviceID", "PowerManagementSupported", "ProviderName", "Purpose", "QuotasDisabled", "QuotasIncomplete", "QuotasRebuilding", "Size", "Status", "StatusInfo", "SupportsDiskQuotas", "SupportsFileBasedCompression", "SystemCreationClassName", "SystemName", "VolumeDirty", "VolumeName", "VolumeSerialNumber")
		uniqueList = "ipAddr, Caption"
		self.wmiQuery("logical disk ", "self.w.Win32_LogicalDisk()", itemList, uniqueList, "logical_disks")
		return
		
	def timezone(self):
		itemList = ("Caption", "Description", "SettingID", "Bias", "DaylightBias", "DaylightDay", "DaylightDayOfWeek", "DaylightHour", "DaylightMillisecond", "DaylightMinute", "DaylightMonth", "DaylightName", "DaylightSecond", "DaylightYear", "StandardBias", "StandardDay", "StandardDayOfWeek", "StandardHour", "StandardMillisecond", "StandardMinute", "StandardMonth", "StandardName", "StandardSecond", "StandardYear")
		uniqueList = "ipAddr"
		self.wmiQuery("time zone", "self.w.Win32_TimeZone()", itemList, uniqueList, "time_zone")
		return
		
	def startup(self):
		itemList = ("Caption", "Description", "SettingID", "Command", "Location", "Name", "User", "UserSID")
		uniqueList = "ipAddr, Caption, UserSID"
		self.wmiQuery("startup program", "self.w.Win32_StartupCommand()", itemList, uniqueList, "startup_programs")
		return

	def profiles(self):
		itemList = ("SID", "LocalPath", "Loaded", "refCount", "Special", "RoamingConfigured", "RoamingPath", "RoamingPreference", "Status", "LastUseTime", "LastDownloadTime", "LastUploadTime", "HealthStatus", "LastAttemptedProfileDownloadTime", "LastAttemptedProfileUploadTime", "LastBackgroundRegistryUploadTime", "AppDataRoaming", "Desktop", "StartMenu", "Documents", "Pictures", "Music", "Videos", "Favorites", "Contacts", "Downloads", "Links", "Searches", "SavedGames")
		uniqueList = "ipAddr, SID, LastUseTime"
		self.wmiQuery("user profile", "self.w.Win32_UserProfile()", itemList, uniqueList, "user_profiles")
		return		
		
	def adapters(self):
		itemList = ("Caption", "Description", "SettingID", "ArpAlwaysSourceRoute", "ArpUseEtherSNAP", "DatabasePath", "DeadGWDetectEnabled", "DefaultIPGateway", "DefaultTOS", "DefaultTTL", "DHCPEnabled", "DHCPLeaseExpires", "DHCPLeaseObtained", "DHCPServer", "DNSDomain", "DNSDomainSuffixSearchOrder", "DNSEnabledForWINSResolution", "DNSHostName", "DNSServerSearchOrder", "DomainDNSRegistrationEnabled", "ForwardBufferMemory", "FullDNSRegistrationEnabled", "GatewayCostMetric", "IGMPLevel", "Index__", "InterfaceIndex", "IPAddress", "IPConnectionMetric", "IPEnabled", "IPFilterSecurityEnabled", "IPPortSecurityEnabled", "IPSecPermitIPProtocols", "IPSecPermitTCPPorts", "IPSecPermitUDPPorts", "IPSubnet", "IPUseZeroBroadcast", "IPXAddress", "IPXEnabled", "IPXFrameType", "IPXMediaType", "IPXNetworkNumber", "IPXVirtualNetNumber", "KeepAliveInterval", "KeepAliveTime", "MACAddress", "MTU", "NumForwardPackets", "PMTUBHDetectEnabled", "PMTUDiscoveryEnabled", "ServiceName", "TcpipNetbiosOptions", "TcpMaxConnectRetransmissions", "TcpMaxDataRetransmissions", "TcpNumConnections", "TcpUseRFC1122UrgentPointer", "TcpWindowSize", "WINSEnableLMHostsLookup", "WINSHostLookupFile", "WINSPrimaryServer", "WINSScopeID", "WINSSecondaryServer")
		uniqueList = "ipAddr, MACAddress"
		self.wmiQuery("network adapter", "self.w.Win32_NetworkAdapterConfiguration()", itemList, uniqueList, "network_adapters")
		return

	def process(self):
		itemList = ("CreationClassName", "Caption", "CommandLine", "CreationDate", "CSCreationClassName", "CSName", "Description", "ExecutablePath", "ExecutionState", "Handle", "HandleCount", "InstallDate", "KernelModeTime", "MaximumWorkingSetSize", "MinimumWorkingSetSize", "Name", "OSCreationClassName", "OSName", "OtherOperationCount", "OtherTransferCount", "PageFaults", "PageFileUsage", "ParentProcessId", "PeakPageFileUsage", "PeakVirtualSize", "PeakWorkingSetSize", "Priority", "PrivatePageCount", "ProcessId", "QuotaNonPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaPeakPagedPoolUsage", "ReadOperationCount", "ReadTransferCount", "SessionId", "Status", "TerminationDate", "ThreadCount", "UserModeTime", "VirtualSize", "WindowsVersion", "WorkingSetSize", "WriteOperationCount", "WriteTransferCount")
		uniqueList = "ipAddr, SessionId, ProcessId"
		self.wmiQuery("process", "self.w.win32_process()", itemList, uniqueList, "processes")
		return
		
	def services(self):
		itemList = ("AcceptPause", "AcceptStop", "Caption", "CheckPoint", "CreationClassName", "DelayedAutoStart", "Description", "DesktopInteract", "DisplayName", "ErrorControl", "ExitCode", "InstallDate", "Name", "PathName", "serviceId", "ServiceSpecificExitCode", "ServiceType", "Started", "StartMode", "StartName", "State", "Status", "SystemCreationClassName", "SystemName", "TagId", "WaitHint")
		uniqueList = "ipAddr, serviceId, Caption"
		self.wmiQuery("services", "self.w.win32_Service()", itemList, uniqueList, "services")
		return	
		
	def shares(self):
		itemList = ("Caption", "Description", "InstallDate", "Status", "AccessMask", "AllowMaximum", "MaximumAllowed", "Name", "Path", "Type")
		uniqueList = "ipAddr, Path"
		self.wmiQuery("shares", "self.w.Win32_Share()", itemList, uniqueList, "shares")
		return

	def pdisks(self):
		itemList = ("Availability", "BytesPerSector", "Capabilities", "CapabilityDescriptions", "Caption", "CompressionMethod", "ConfigManagerErrorCode", "ConfigManagerUserConfig", "CreationClassName", "DefaultBlockSize", "Description", "DeviceID", "ErrorCleared", "ErrorDescription", "ErrorMethodology", "FirmwareRevision", "Index__", "InstallDate", "InterfaceType", "LastErrorCode", "Manufacturer", "MaxBlockSize", "MaxMediaSize", "MediaLoaded", "MediaType", "MinBlockSize", "Model", "Name", "NeedsCleaning", "NumberOfMediaSupported", "Partitions", "PNPDeviceID", "PowerManagementCapabilities", "PowerManagementSupported", "SCSIBus", "SCSILogicalUnit", "SCSIPort", "SCSITargetId", "SectorsPerTrack", "SerialNumber", "Signature", "Size", "Status", "StatusInfo", "SystemCreationClassName", "SystemName", "TotalCylinders", "TotalHeads", "TotalSectors", "TotalTracks", "TracksPerCylinder")
		uniqueList = "ipAddr, DeviceID"
		self.wmiQuery("physical disk", "self.w.Win32_DiskDrive()", itemList, uniqueList, "physical_disks")
		return
		
	def memory(self):
		itemList = ("Attributes", "BankLabel", "Capacity", "Caption", "ConfiguredClockSpeed", "ConfiguredVoltage", "CreationClassName", "DataWidth", "Description", "DeviceLocator", "FormFactor", "HotSwappable", "InstallDate", "InterleaveDataDepth", "InterleavePosition", "Manufacturer", "MaxVoltage", "MemoryType", "MinVoltage", "Model", "Name", "OtherIdentifyingInfo", "PartNumber", "PositionInRow", "PoweredOn", "Removable", "Replaceable", "SerialNumber", "SKU", "SMBIOSMemoryType", "Speed", "Status", "Tag", "TotalWidth", "TypeDetail", "Version")
		uniqueList = "ipAddr, SerialNumber, DeviceLocator"
		self.wmiQuery("physical memory", "self.w.Win32_PhysicalMemory()", itemList, uniqueList, "physical_memory")
		return
		
	def patches(self):
		itemList = ("Caption", "Description", "InstallDate", "Name", "Status", "CSName", "FixComments", "HotFixID", "InstalledBy", "InstalledOn", "ServicePackInEffect")
		uniqueList = "ipAddr, Caption"
		self.wmiQuery("patch", "self.w.Win32_QuickFixEngineering()", itemList, uniqueList, "patch_data")
		return		
		
	def bios(self):
		itemList = ("BiosCharacteristics", "BIOSVersion", "BuildNumber", "Caption", "CodeSet", "CurrentLanguage", "Description", "EmbeddedControllerMajorVersion", "EmbeddedControllerMinorVersion", "IdentificationCode", "InstallableLanguages", "InstallDate", "LanguageEdition", "ListOfLanguages", "Manufacturer", "Name", "OtherTargetOS", "PrimaryBIOS", "ReleaseDate", "SerialNumber", "SMBIOSBIOSVersion", "SMBIOSMajorVersion", "SMBIOSMinorVersion", "SMBIOSPresent", "SoftwareElementID", "SoftwareElementState", "Status", "SystemBiosMajorVersion", "SystemBiosMinorVersion", "TargetOperatingSystem", "Version")
		uniqueList = "ipAddr, BIOSVersion"
		self.wmiQuery("BIOS", "self.w.Win32_BIOS()", itemList, uniqueList, "bios_data")
		return
		
	def pnp(self):
		itemList = ("Availability", "Caption", "ClassGuid", "CompatibleID", "ConfigManagerErrorCode", "ConfigManagerUserConfig", "CreationClassName", "Description", "DeviceID", "ErrorCleared", "ErrorDescription", "HardwareID", "InstallDate", "LastErrorCode", "Manufacturer", "Name", "PNPClass", "PNPDeviceID", "PowerManagementCapabilities", "PowerManagementSupported", "Present", "Service", "Status", "StatusInfo", "SystemCreationClassName", "SystemName")
		uniqueList = "ipAddr, ClassGuid"
		self.wmiQuery("PlugNPlay", "self.w.Win32_PNPEntity()", itemList, uniqueList, "plugnplay")
		return
		
	def drivers(self):
		itemList = ("AcceptPause", "AcceptStop", "Caption", "CreationClassName", "Description", "DesktopInteract", "DisplayName", "ErrorControl", "ExitCode", "InstallDate", "Name", "PathName", "ServiceSpecificExitCode", "ServiceType", "Started", "StartMode", "StartName", "State", "Status", "SystemCreationClassName", "SystemName", "TagId")
		uniqueList = "ipAddr, PathName"
		self.wmiQuery("driver", "self.w.Win32_SystemDriver()", itemList, uniqueList, "system_drivers")
		return
		
	def processors(self):
		itemList = ("AddressWidth", "Architecture", "AssetTag", "Availability", "Caption", "Characteristics", "ConfigManagerErrorCode", "ConfigManagerUserConfig", "CpuStatus", "CreationClassName", "CurrentClockSpeed", "CurrentVoltage", "DataWidth", "Description", "DeviceID", "ErrorCleared", "ErrorDescription", "ExtClock", "Family", "InstallDate", "L2CacheSize", "L2CacheSpeed", "L3CacheSize", "L3CacheSpeed", "LastErrorCode", "Level", "LoadPercentage", "Manufacturer", "MaxClockSpeed", "Name", "NumberOfCores", "NumberOfEnabledCore", "NumberOfLogicalProcessors", "OtherFamilyDescription", "PartNumber", "PNPDeviceID", "PowerManagementCapabilities", "PowerManagementSupported", "ProcessorId", "ProcessorType", "Revision", "Role", "SecondLevelAddressTranslationExtensions", "SerialNumber", "SocketDesignation", "Status", "StatusInfo", "Stepping", "SystemCreationClassName", "SystemName", "ThreadCount", "UniqueId", "UpgradeMethod", "Version", "VirtualizationFirmwareEnabled", "VMMonitorModeExtensions", "VoltageCaps")
		uniqueList = "ipAddr, SerialNumber"
		self.wmiQuery("processor", "self.w.Win32_Processor()", itemList, uniqueList, "processors")
		
	def os(self):
		itemList = ("BootDevice", "BuildNumber", "BuildType", "Caption", "CodeSet", "CountryCode", "CreationClassName", "CSCreationClassName", "CSDVersion", "CSName", "CurrentTimeZone", "DataExecutionPrevention_Available", "DataExecutionPrevention_32BitApplications", "DataExecutionPrevention_Drivers", "DataExecutionPrevention_SupportPolicy", "Debug", "Description", "Distributed", "EncryptionLevel", "FreePhysicalMemory", "FreeSpaceInPagingFiles", "FreeVirtualMemory", "InstallDate", "LargeSystemCache", "LastBootUpTime", "LocalDateTime", "Locale", "Manufacturer", "MaxNumberOfProcesses", "MaxProcessMemorySize", "MUILanguages", "Name", "NumberOfLicensedUsers", "NumberOfProcesses", "NumberOfUsers", "OperatingSystemSKU", "Organization", "OSArchitecture", "OSLanguage", "OSProductSuite", "OSType", "OtherTypeDescription", "PAEEnabled", "PlusProductID", "PlusVersionNumber", "PortableOperatingSystem", "Primary__", "ProductType", "RegisteredUser", "SerialNumber", "ServicePackMajorVersion", "ServicePackMinorVersion", "SizeStoredInPagingFiles", "Status", "SuiteMask", "SystemDevice", "SystemDirectory", "SystemDrive", "TotalSwapSpaceSize", "TotalVirtualMemorySize", "TotalVisibleMemorySize", "Version", "WindowsDirectory", "QuantumLength", "QuantumType")
		uniqueList = "ipAddr"
		self.wmiQuery("operating system", "self.w.Win32_OperatingSystem()", itemList, uniqueList, "operating_system")	
		
	def products(self):
		itemList = ("AssignmentType", "Caption", "Description", "IdentifyingNumber", "InstallDate", "InstallDate2", "InstallLocation", "InstallState", "HelpLink", "HelpTelephone", "InstallSource", "Language", "LocalPackage", "Name", "PackageCache", "PackageCode", "PackageName", "ProductID", "RegOwner", "RegCompany", "SKUNumber", "Transforms", "URLInfoAbout", "URLUpdateInfo", "Vendor", "WordCount", "Version")
		uniqueList = "ipAddr, IdentifyingNumber"
		self.wmiQuery("products", "self.w.Win32_Product()", itemList, uniqueList, "products")
		
	def vss(self):
		itemList = ("Caption", "Description", "ID", "InstallDate", "Name", "SetID", "ProviderID", "Status", "Count", "DeviceObject", "VolumeName", "OriginatingMachine", "ServiceMachine", "ExposedName", "State", "Persistent", "ClientAccessible", "NoAutoRelease", "NoWriters", "Transportable", "NotSurfaced", "HardwareAssisted", "Differential", "Plex", "Imported", "ExposedRemotely", "ExposedLocally")
		uniqueList = ("ipAddr, ID")
		self.wmiQuery("Volume Shadow Copies", "self.w.win32_shadowcopy()", itemList, uniqueList, "vss")