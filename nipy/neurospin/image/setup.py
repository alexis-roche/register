#!/usr/bin/env python

def configuration(parent_package='',top_path=None):
    
    from numpy.distutils.misc_util import Configuration

    config = Configuration('image', parent_package, top_path)
    config.add_data_dir('tests')
    config.add_data_dir('benchmarks')
    config.add_extension('interp_module', sources=['interp_module.c', 'cubic_spline.c'])

    return config


if __name__ == '__main__':
    print 'This is the wrong setup.py file to run'


