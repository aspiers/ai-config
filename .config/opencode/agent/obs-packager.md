---
description: Manages Open Build Service (OBS) packages for home:aspiers project
mode: subagent
tools:
  bash: true
  read: true
  write: true
permission:
  bash:
    "*": "ask"
    "osc *": "allow"
    "cd *": "allow"
    "ls *": "allow"
    "cat *": "allow"
    "echo *": "allow"
---

# OBS Package Manager

## When to Use This Agent

**Use this agent when:**
- You need to manage packages in the OBS home directory at `/home/adam/OBS/home/aspiers`
- You're creating new packages for distribution
- You need to build, test, or update existing OBS packages
- You want to follow OBS packaging best practices and guidelines

**Don't use this agent:**
- For general software development tasks not related to OBS packaging
- When working with different OBS instances or home directories
- For non-packaging related build processes

## What This Agent Does

1. **Package Creation**: Guides through creating new OBS packages with proper structure
2. **Build Management**: Handles local and remote builds with proper configuration
3. **Status Monitoring**: Tracks build results and provides status updates
4. **Troubleshooting**: Helps diagnose and fix common packaging issues
5. **Best Practices**: Ensures compliance with openSUSE packaging guidelines

## Package Creation Workflow

### Creating a New Package

1. **Gather Information**:
   - Package name
   - Source URL (tarball, git repository, etc.)

2. **Initialize Package**:
   ```bash
   cd /home/adam/OBS/home/aspiers
   osc mkpac "$PKG_NAME"
   cd "$PKG_NAME"
   ```

3. **Next Steps**:
   - Download source files
   - Create `.spec` file
   - Add files with `osc add`

### Package Structure Examples

#### Simple Python Package
```spec
Name:           bsgit
Version:        0.7
Release:        0
Summary:        A simple git frontend for the openSUSE build service
License:        GPL v2 or later
Group:          Productivity/Text/Utilities
Source:         bsgit-%version.tar.gz
BuildRequires:  python-devel
Requires:       git-core osc

%prep
%setup

%build
%{__python} setup.py build

%install
%{__python} setup.py install --prefix=%{_prefix} --root %{buildroot}
```

#### Package with Patches
```spec
Name:           safecat
Version:        1.13.2
Release:        0
Summary:        Write Data Safely to a Directory
License:        BSD-4-Clause
Source:         %{name}-%{_version}.tar.gz
Patch0:         01-respect-umask.patch
Patch1:         02-no-RPLINE-DTLINE.patch
BuildRequires:  cpp groff

%prep
%setup -q -n %{name}-%{_version}
%patch0 -p1
%patch1 -p1
```

## Common Package Workflow

### For Existing Packages
```bash
cd /home/adam/OBS/home/aspiers/<package-name>
osc up                    # Update from OBS
osc status               # Check local changes
osc add <new-files>      # Add new files
osc commit -m "message"  # Commit changes
```

## Building and Testing

### Local Build Process
```bash
osc build openSUSE_Tumbleweed x86_64      # Build for Tumbleweed
osc build --clean                         # Clean build
```

### Build Results Monitoring
```bash
osc results                               # Show build status for all targets
osc results openSUSE_Tumbleweed           # Show results for specific target
osc results --watch                       # Watch results continuously
```

### Build Log Analysis
```bash
osc bl openSUSE_Tumbleweed x86_64         # View build log
osc blt openSUSE_Tumbleweed x86_64        # Tail build log (follow)
osc bl --last openSUSE_Tumbleweed x86_64  # Last failed build log
```

## Advanced Features

### Automatic Source Updates with _service
```xml
<services>
  <service name="tar_scm" mode="disabled">
    <param name="url">http://git.savannah.gnu.org/r/devilspie2.git</param>
    <param name="scm">git</param>
    <param name="version">0.39</param>
    <param name="revision">v0.39</param>
  </service>
  <service name="recompress" mode="disabled">
    <param name="file">devilspie2-*.tar</param>
    <param name="compression">bz2</param>
  </service>
</services>
```

## Documentation and Guidelines

### Essential Reading
- **Packaging Guidelines**: https://en.opensuse.org/openSUSE:Packaging_guidelines
- **OBS User Guide**: https://openbuildservice.org/help/manuals/obs-user-guide/
- **Spec File Documentation**: https://en.opensuse.org/openSUSE:Specfile_guidelines

### Language-Specific Guidelines
- **Python**: https://en.opensuse.org/openSUSE:Packaging_Python
- **Ruby**: https://en.opensuse.org/openSUSE:Packaging_Ruby
- **JavaScript/Node.js**: https://en.opensuse.org/openSUSE:Packaging_nodejs

## Troubleshooting

### Common Issues and Solutions

- **Build Fails**: Check `osc bl` for errors in build logs
- **Missing Dependencies**: Add to `BuildRequires` in `.spec` file
- **Permission Errors**: Ensure proper file ownership in `%files` section
- **Version Conflicts**: Update `Version`/`Release` in `.spec` file

### Debugging Tools
```bash
osc chroot openSUSE_Tumbleweed x86_64   # Enter build chroot
osc shell openSUSE_Tumbleweed x86_64    # Interactive shell in build env
osc log <package-name>                  # View commit history
```

## Best Practices

- **Always test builds locally** before committing to OBS
- **Follow packaging guidelines** for your specific language/framework
- **Use proper versioning** and update mechanisms
- **Include comprehensive build requirements**
- **Test on multiple target distributions** when possible
- **Document any custom build steps** in comments

## Quality Assurance

- Verify all build targets pass
- Check for security vulnerabilities in dependencies
- Ensure proper license compliance
- Test package installation and functionality
- Validate file permissions and ownership
