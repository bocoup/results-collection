from buildbot.plugins import util

@util.renderer
def makeWptRunCommand(properties):
    browser_id = None
    browser_name = properties.getProperty('browser_name')
    command = [
        'echo',
        './wpt', 'run',
        '--no-restart-on-unexpected',
        '--log-wptreport', properties.getProperty('log_wptreport'),
        '--log-raw', properties.getProperty('log_raw'),
        '--this-chunk', properties.getProperty('this_chunk'),
        '--total-chunks', properties.getProperty('total_chunks')
    ]

    if properties.getProperty('os_name') != 'linux':
        if browser_name is 'edge':
            sauce_browser_name = 'MicrosoftEdge'
        else:
            sauce_browser_name = browser_name

        browser_id = util.Interpolate(
            'sauce:%(kw:sauce_browser_name)s:%(prop:browser_version)s',
            sauce_browser_name=sauce_browser_name
        )
        sauce_platform_id = util.Interpolate(
            '%(prop:os_name)s %(prop:os_version)s'
        )

        command.extend([
            '--sauce-platform', sauce_platform_id,
            '--sauce-user', util.Interpolate('%(secret:sauce_labs_user)s'),
            '--sauce-key', util.Interpolate('%(secret:sauce_labs_key)s'),
            '--sauce-tunnel-id', properties.getProperty('workername'),
            '--sauce-connect-binary', 'sc'
        ])
    else:
        command = ['xvfb-run', '--auto-servernum'] + command

        browser_id = browser_name

    command.append(browser_id)

    return command
