<file>
<absolute_file_name>/app/frontend/src/components/HeroBanner.js</absolute_file_name>
<content_insert>
<![CDATA[
AFTER_PATTERN:        </div>\n\n        {/* Clocks + Market */}

        {/* Date + Weather */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          <div className="glass-panel p-4 h-full flex items-center justify-between">
            <div className="text-white/90 font-semibold text-base sm:text-lg">{todayLocal}</div>
            <div className="text-xs text-gray-400">{Intl.DateTimeFormat().resolvedOptions().timeZone}</div>
          </div>
          <div className="h-full"><WeatherWidget /></div>
        </div>
]]>
</content_insert>
</file>