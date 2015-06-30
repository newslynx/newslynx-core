"""
An interactive configuration creator.
"""
import sys 
import os 
import re

re_conf = '{}:[^\n]+'

def setup(parser):
    conf_parser = parser.add_parser("config", help="Spawns the dynamic scheduling daemon.")
    return 'config', run



def run(opts, log, **kwargs):
    logo = """
     / \ / \ / \ / \ / \ / \ / \ / \ 
    ( n | e | w | s | l | y | n | x )
     \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/
    """  

    from sqlalchemy import create_engine
    from newslynx.defaults import _DEFAULT_CONFIG, _CONFIG_REQUIRES
    try:
        from newslynx.settings import CONFIG_FILE as config_file
    except Exception:
        from newslynx.defaults import CONFIG_FILE as default_config_file
        config_file = None
    if not config_file:
        config_file = default_config_file
    from newslynx.lib.serialize import yaml_to_obj

    try:
        log.info(logo +"\n", line=False, color='lightwhite_ex')
        log.info('Would you like to configure NewsLynx now ?', line=False, color="blue")
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

            log.info('\nNo configurations exist in: \n', line=False, color="yellow")
            log.info(config_file, color='magenta', line=False)

            log.info('\nGenerating default config file in: \n', line=False, color="yellow")
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
        
        # check required configs
        for k in _CONFIG_REQUIRES:
            val = conf_obj.get(k)
            log.info('\nOkay to use ', line=False, color="blue")
            log.info(val, line=False, color="green")
            log.info(' for your ', line=False, color='blue')
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


        log.info('\nStoring new configurations to:\n', line=False, color="blue")
        log.info(config_file +"\n", color='magenta', line=False)
        with open(config_file, 'wb') as f:
            f.write(conf_str)

        log.info('\nNow run ', line=False, color="blue")
        log.info("newslynx init \n", color="green", line=False)
        sys.exit(0)

    except KeyboardInterrupt as e:
        log.warning('\nInterrupted by user, exiting\n', line=False)
        sys.exit(2) # interrupt