<file>
<absolute_file_name>/app/frontend/src/components/NewsSection.js</absolute_file_name>
<content_replace>
<![CDATA[
REPLACE:                  <div className="text-[11px] text-gray-400 mt-1">
                    {it.source && <span className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 mr-2">{it.source}</span>}
                    {it.published && <span>{new Date(it.published).toLocaleString()}</span>}
                  </div>
WITH:                  <div className="text-[11px] text-gray-400 mt-1 flex items-center gap-2">
                    {it.source && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/5 border border-white/10 mr-1">
                        <img src={`https://logo.clearbit.com/${it.source}`} alt="src" className="w-3 h-3 rounded" onError={(e)=>{e.currentTarget.style.display='none';}} />
                        <span>{it.source}</span>
                      </span>
                    )}
                    {it.published && <span>{new Intl.RelativeTimeFormat('en', { numeric: 'auto' }).format(Math.round((new Date(it.published).getTime()-Date.now())/60000), 'minute')}</span>}
                  </div>
]]>
</content_replace>
</file>