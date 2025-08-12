<file>
<absolute_file_name>/app/frontend/src/components/NavBar.js</absolute_file_name>
<content_replace>
<![CDATA[
REPLACE:  return (
    <header className="sticky top-0 z-50">
      <div className="bg-[#070a11]/98">
WITH:  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 4);
    onScroll();
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header className="sticky top-0 z-[2000]">
      <div className={`${scrolled ? 'bg-[#070a11]/98 shadow-lg border-b border-white/10' : 'bg-[#070a11]/90'} transition-colors` }>
]]>
</content_replace>
</file>