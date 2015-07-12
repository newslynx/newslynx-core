"""
An interactive configuration creator.
"""

import sys 
import os 
import re

re_conf = '{}:[^\n]+'

def setup(parser):
    conf_parser = parser.add_parser("config", help="Setup your .newslynx config file.")
    return 'config', run


def run(opts, log, **kwargs):

    ## First lazy load all the libraries
    ## and catch import errors.
    from sqlalchemy import create_engine
    from newslynx.defaults import (
        _DEFAULT_CONFIG, _CONFIG_REQUIRES, _DEFAULT_DEFAULTS)
    try:
        from newslynx.settings import CONFIG_FILE as config_file
        from newslynx.settings import DEFAULT_TAGS as tags_file
        from newslynx.settings import DEFAULT_RECIPES as recipes_file
    
    except Exception:
        from newslynx.defaults import CONFIG_FILE as default_config_file
        from newslynx.defaults import DEFAULT_TAGS as default_tags_file
        from newslynx.defaults import DEFAULT_RECIPES as default_recipes_file
        config_file = None
        tags_file = None
        recipes_file = None

    # if custom settings are missing, use defaults.
    if not config_file:
        config_file = default_config_file
    if not tags_file:
        tags_file = default_tags_file
    if not recipes_file:
        recipes_file = default_recipes_file

    from newslynx.lib.serialize import yaml_to_obj

    # are we re-configuring?
    reconf = ""
    if kwargs.get('re', True):
        reconf = "re-"

    try:

        # Deal with location of configurations.

        log.info('Would you like to {}configure NewsLynx now ?'.format(reconf), line=False, color="blue")
        log.info(' y/(n): ', line=False, color='yellow')
        resp = raw_input("")
        if not resp.startswith('y'):
            log.warning('Goodbye!\n', line=False)
            sys.exit(1)

        log.info('\nUsing configurations in: \n', line=False, color="blue")
        log.info(config_file, color='magenta', line=False)

        try:
            conf_str = open(config_file).read()
            conf_obj = yaml_to_obj(conf_str)
        
        except Exception as e:

            # Load in defaults if missing.

            log.info('\n\nNo configurations exist in: \n', line=False, color="yellow")
            log.info(config_file, color='magenta', line=False)

            log.info('\n\nGenerating default config file in: \n', line=False, color="yellow")
            log.info(config_file, color='magenta', line=False)

            config_dir = "/".join(config_file.split('/')[:-1])
            try:
                os.makedirs(config_dir)
            except OSError:
                pass
            with open(config_file, 'wb') as f1:
                with open(_DEFAULT_CONFIG, 'rb') as f2:
                    conf_str = f2.read()
                    conf_obj = yaml_to_obj(conf_str)
                    f1.write(conf_str)
        log.info("\n", color=None, line=False)

        # Reset Required Keys
        
        # check required configs
        for k in _CONFIG_REQUIRES:
            val = conf_obj.get(k)
            log.info('\nOkay to use ', line=False, color="blue")
            log.info(val, line=False, color="green")
            log.info('\nfor your ', line=False, color='blue')
            log.info(k, line=False, color="magenta")
            log.info(' ? ', line=False, color="blue")
            log.info(' y/(n): ', line=False, color='yellow')
            resp = raw_input("")
            if not resp.startswith('y'):
                log.info('Enter your ', line=False, color="blue")
                log.info(k, line=False, color='magenta')
                log.info(" : ", color="blue", line=False)
                val = raw_input(" ")

                if "database_uri" in k:
                    while 1:
                        try:
                            engine = create_engine(val)
                            engine.connect()
                            break
                        except:
                            log.info('Cannot connect to ', line=False, color="blue")
                            log.info(val, line=False, color="magenta")
                            log.warning('\nTry again: ', line=False)
                            val = raw_input(" ")
                cx = re.compile(re_conf.format(k))
                newval = "{}: {}".format(k, val)
                m = cx.search(conf_str)
                if m:
                    conf_str = cx.sub(newval, conf_str)
                else:
                    conf_str += "\n" + newval
        
        # Install default tags and recipes

        log.info('\nWould you like to use our default tags and recipes? ', color='blue', line=False)
        log.info(' y/(n): ', line=False, color='yellow')
        resp = raw_input("")
        modules = [
            ('default_tags', tags_file),
            ('default_recipes', recipes_file)
        ]
        if resp.startswith('y'):
            for k, m in modules:
                m = os.path.expanduser(m)
                parts  = m.split('/')
                default_dir = "/".join(parts[:-1])
                path  = parts[-1]
                name = parts[-1].split('.')[0]
                try:
                    os.makedirs(default_dir)
                except OSError:
                    pass
                
                log.info('\nStoring default ', line=False, color="yellow")
                log.info(name, line=False, color='green')
                log.info(' in:\n', line=False, color="blue")
                log.info(m +"\n", line=False, color='magenta')
               
                with open(m, 'wb') as f1:
                    with open(os.path.join(_DEFAULT_DEFAULTS, path), 'rb') as f2:
                        f1.write(f2.read())

                cx = re.compile(re_conf.format(k))
                newval = "{}: {}".format(k, m)
                m = cx.search(conf_str)
                if m:
                    conf_str = cx.sub(newval, conf_str)
                else:
                    conf_str += "\n" + newval
        else: 
            pass

        # Write updated config

        log.info('\nStoring new configurations to:\n', line=False, color="blue")
        log.info(config_file +"\n", color='magenta', line=False)
        with open(config_file, 'wb') as f:
            f.write(conf_str)

        log.info("\nYou can change these configurations at any time by modifying:\n", line=False, color="blue")
        log.info(config_file, line=False, color='magenta')

        # What to do next?

        log.info('\n\nNow run ', line=False, color="blue")
        log.info("newslynx init ", color="green", line=False)
        log.info("to get started \n", color="blue", line=False)
        sys.exit(0)

    except KeyboardInterrupt as e:
        log.warning('\nInterrupted by user.\n', line=False)
        sys.exit(2) # interrupt