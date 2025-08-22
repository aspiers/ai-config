Open Build Service (OBS) project management commands for home:aspiers

This command helps manage packages in the OBS home directory at
/home/adam/OBS/home/aspiers

## Setup and Basic Commands

### Create a new package:
```bash
read -p "Package name: " PKG_NAME
read -p "Source URL (tarball, git repo, etc.): " SOURCE_URL
cd /home/adam/OBS/home/aspiers
osc mkpac "$PKG_NAME"
cd "$PKG_NAME"
echo "Package $PKG_NAME created. Source: $SOURCE_URL"
echo "Next steps: download source, create .spec file, add files with 'osc add'"
```

### Common workflow for existing packages:
```bash
cd /home/adam/OBS/home/aspiers/<package-name>
osc up                    # Update from OBS
osc status               # Check local changes
osc add <new-files>      # Add new files
osc commit -m "message"  # Commit changes
```

## Building and Testing

### Build locally (takes 1-2+ minutes):
```bash
osc build openSUSE_Tumbleweed x86_64      # Build for Tumbleweed
osc build --clean                         # Clean build
```

### Monitor build results:
```bash
osc results                               # Show build status for all targets
osc results openSUSE_Tumbleweed           # Show results for specific target
osc results --watch                       # Watch results continuously
```

### Check build logs:
```bash
osc bl openSUSE_Tumbleweed x86_64         # View build log
osc blt openSUSE_Tumbleweed x86_64        # Tail build log (follow)
osc bl --last openSUSE_Tumbleweed x86_64  # Last failed build log
```

## Package Structure Examples

### Simple Python package (bsgit):
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

### Package with patches (safecat):
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

### Using _service for automatic source updates:
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

Essential reading:
- **Packaging Guidelines**: https://en.opensuse.org/openSUSE:Packaging_guidelines
- **OBS User Guide**: https://openbuildservice.org/help/manuals/obs-user-guide/
- **Spec file documentation**: https://en.opensuse.org/openSUSE:Specfile_guidelines

Language-specific guidelines:
- **Python**: https://en.opensuse.org/openSUSE:Packaging_Python
- **Ruby**: https://en.opensuse.org/openSUSE:Packaging_Ruby
- **JavaScript/Node.js**: https://en.opensuse.org/openSUSE:Packaging_nodejs

## Troubleshooting

### Common issues:
- Build fails: Check `osc bl` for errors
- Missing dependencies: Add to BuildRequires in .spec file
- Permission errors: Ensure proper file ownership in %files section
- Version conflicts: Update Version/Release in .spec file

### Useful debugging:
```bash
osc chroot openSUSE_Tumbleweed x86_64   # Enter build chroot
osc shell openSUSE_Tumbleweed x86_64    # Interactive shell in build env
osc log <package-name>                  # View commit history
```

Remember to always test builds locally before committing to OBS!