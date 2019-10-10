# Copyright 2019 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from ament_index_python import get_packages_with_prefixes
from catkin_pkg.package import InvalidPackage
from catkin_pkg.package import parse_package
from ros2doctor.api import DoctorCheck
from ros2doctor.api import DoctorReport
from ros2doctor.api import Report
from ros2doctor.api import Result

import rosdistro


def get_ros_packages_info() -> dict:
    """
    Return all current distro's packages info using rosdistro API.

    :return: a dictionary contains package name, release, source and status
    """
    distro_name = os.environ.get('ROS_DISTRO')
    distro_name = distro_name.lower()
    url = rosdistro.get_index_url()
    i = rosdistro.get_index(url)
    distro_data = rosdistro.get_distribution(i, distro_name).get_data()
    return distro_data.get('repositories')


class PackageCheck(DoctorCheck):
    """Check local package versions against release versions on rosdistro."""

    def category(self):
        return 'package'

    def check(self):
        """Check packages within the directory where command is called."""
        result = Result()
        try:
            distro_packages_info = get_ros_packages_info()
        except AttributeError:
            result.add_error('ERROR: Unable to obtain current distro package information \
                from rosdistro.')
            return result
        local_packages_prefixes = get_packages_with_prefixes()
        if not local_packages_prefixes or not distro_packages_info:
            result.add_error('ERROR: local packages info or distro packages info is empty.')
            return result
        for package_name, package_prefix in local_packages_prefixes.items():
            file_path = os.path.join(package_prefix, 'share', package_name)
            if package_name in distro_packages_info:
                try:
                    package_info = distro_packages_info.get(package_name)
                    required_ver = package_info.get('release').get('version')
                except AttributeError:
                    result.add_warning('`%s` is not found in distribution release list.'
                                       % package_name)
                    required_ver = ''
            try:
                package_obj = parse_package(file_path)
                local_ver = package_obj.version
            except (AttributeError, IOError, InvalidPackage):
                result.add_warning('Unable to parse `%s` package.xml file.' % package_name)
                local_ver = ''
            if required_ver and local_ver:
                if required_ver[:3] != package_obj.version[:3]:
                    result.add_warning('%s local version %s does not match required version %s.'
                                       % (package_name, package_obj.version, required_ver))
        return result


class PackageReport(DoctorReport):
    """Report local package versions and release versions on rosdistro."""

    def category(self):
        return 'package'

    def report(self):
        """Report packages within the directory where command is called."""
        report = Report('PACKAGE VERSIONS')
        try:
            distro_packages_info = get_ros_packages_info()
        except AttributeError:
            return report
        local_package_prefixes = get_packages_with_prefixes()
        if distro_packages_info and local_package_prefixes:
            for package_name, package_prefix in local_package_prefixes.items():
                try:
                    package_info = distro_packages_info.get(package_name)
                    required_ver = package_info.get('release').get('version')
                except AttributeError:
                    required_ver = ''
                file_path = os.path.join(package_prefix, 'share', package_name)
                try:
                    package_obj = parse_package(file_path)
                    local_ver = package_obj.version
                except (IOError, InvalidPackage):
                    local_ver = ''
                report.add_to_report(package_name, 'required='+required_ver+', local='+local_ver)
        return report
