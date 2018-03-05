from buildbot.plugins import util

@util.renderer
def makeWptRunCommand(properties):
    wpt_platform_id = None
    browser_name = properties.getProperty('browser')
    command = [
        'echo',
        './wpt', 'run',
        '--no-restart-on-unexpected',
        '--log-wptreport', properties.getProperty('log_wptreport'),
        '--this-chunk', properties.getProperty('this_chunk'),
        '--total-chunks', properties.getProperty('total_chunks')
    ]

    if browser_name in ('edge', 'safari'):
        browser_version = properties.getProperty('browser_version')
        wpt_platform_id = util.Interpolate(
            'sauce:%(kw:browser_name)s:%(kw:browser_version)s',
            browser_name=browser_name,
            browser_version=browser_version
        )
        sauce_platform_id = util.Interpolate(
            '%(kw:browser_name)s %(kw:browser_version)s',
            browser_name=browser_name,
            browser_version=browser_version
        )

        command.extend([
            '--sauce-platform', sauce_platform_id,
            '--sauce-user', util.Interpolate('%(secret:sauce_labs_user)s'),
            '--sauce-key', util.Interpolate('%(secret:sauce_labs_key)s'),
            '--sauce-tunnel-id', properties.getProperty('workername'),
            '--sauce-connect-binary', 'sc'
        ])
    else:
        wpt_platform_id = browser_name

    command.append(wpt_platform_id)

    return command
