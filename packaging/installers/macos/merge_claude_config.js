ObjC.import('Foundation');

function backupIfExists(path) {
  const fm = $.NSFileManager.defaultManager;
  if (fm.fileExistsAtPath(path)) {
    const backupPath = path + '.bak';
    fm.removeItemAtPathError(backupPath, $());
    const ok = fm.copyItemAtPathToPathError(path, backupPath, $());
    if (!ok) {
      throw new Error('failed to create backup: ' + backupPath);
    }
  }
}

function readFile(path) {
  const fm = $.NSFileManager.defaultManager;
  if (!fm.fileExistsAtPath(path)) return null;
  const data = fm.contentsAtPath(path);
  if (!data) {
    throw new Error('failed to read file (exists but unreadable): ' + path);
  }
  const nsString = $.NSString.alloc.initWithDataEncoding(data, $.NSUTF8StringEncoding);
  if (nsString.isNil()) {
    throw new Error('failed to decode file as UTF-8: ' + path);
  }
  return ObjC.unwrap(nsString);
}

function writeFile(path, text) {
  const fm = $.NSFileManager.defaultManager;
  const dir = path.substring(0, path.lastIndexOf('/'));
  const dirOk = fm.createDirectoryAtPathWithIntermediateDirectoriesAttributesError(dir, true, $(), $());
  if (!dirOk) {
    throw new Error('failed to create directory: ' + dir);
  }
  const nsStr = $.NSString.alloc.initWithUTF8String(text);
  const writeOk = nsStr.writeToFileAtomicallyEncodingError(path, true, $.NSUTF8StringEncoding, $());
  if (!writeOk) {
    throw new Error('failed to write file: ' + path);
  }
}

function run(argv) {
  const [configPath, serverName, command, envName, envValue] = argv;

  backupIfExists(configPath);

  let config = {};
  const existing = readFile(configPath);
  if (existing) {
    config = JSON.parse(existing);
  }
  if (!config.mcpServers) config.mcpServers = {};

  config.mcpServers[serverName] = { command: command, env: {} };
  config.mcpServers[serverName].env[envName] = envValue;

  writeFile(configPath, JSON.stringify(config, null, 2));
  return "OK";
}
