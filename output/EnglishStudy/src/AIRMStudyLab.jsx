const { useState, useEffect } = React;

/**
 * AIRM Study Lab: 5-Pass 认知引擎
 * 状态驱动交互：Pass 0 (Scanning) -> Pass 4 (Zen)
 */
const AIRMStudyLab = () => {
  const [pass, setPass] = useState(0);
  const [selectedNode, setSelectedNode] = useState(null);

  const passLabels = ["Scanning", "Decoding", "Mapping", "Acquisition", "Zen"];

  const theme = window.EnglishStudyTheme;

  const styles = {
    container: {
      display: 'grid',
      gridTemplateColumns: '1fr 320px',
      gap: theme.spacing.golden,
      height: '90vh',
      padding: theme.spacing.golden,
      backgroundColor: theme.colors.paper,
      color: theme.colors.ink,
      fontFamily: theme.typography.serif,
      transition: 'all 0.6s cubic-bezier(0.2, 0, 0, 1)'
    },
    article: {
      fontSize: '1.25rem',
      lineHeight: '1.8',
      maxWidth: '720px',
      margin: '0 auto',
      opacity: pass === 4 ? 0.9 : 1,
      filter: pass === 0 ? 'blur(0.5px)' : 'none'
    },
    sidebar: {
      borderLeft: `1px solid ${theme.colors.subtle}`,
      paddingLeft: theme.spacing.golden,
      fontFamily: theme.typography.sans,
      display: pass === 4 ? 'none' : 'block'
    },
    passIndicator: {
      position: 'fixed',
      bottom: '2rem',
      left: '50%',
      transform: 'translateX(-50%)',
      display: 'flex',
      gap: '1rem',
      backgroundColor: 'white',
      padding: '0.5rem 1.5rem',
      borderRadius: '100px',
      boxShadow: `0 10px 30px ${theme.colors.shadow}`,
      zIndex: 1000
    },
    dot: (active) => ({
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      backgroundColor: active ? theme.colors.accent : theme.colors.subtle,
      transition: 'all 0.3s ease'
    })
  };

  return (
    <div style={styles.container}>
      {/* 5-Pass 状态导航器 */}
      <div style={styles.passIndicator}>
        {passLabels.map((label, idx) => (
          <div 
            key={idx} 
            onClick={() => setPass(idx)}
            style={{cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px'}}
          >
            <div style={styles.dot(pass === idx)} />
            <span style={{fontSize: '12px', color: pass === idx ? theme.colors.ink : theme.colors.subtle}}>
              {pass === idx ? label : ''}
            </span>
          </div>
        ))}
      </div>

      {/* 主阅读区 */}
      <main style={styles.article}>
        <h1 style={{fontSize: '2.5rem', marginBottom: '2rem', fontWeight: 400}}>
          The Architecture of Neural Cognition
        </h1>
        <p>
          In the realm of advanced AI systems, the bridge between raw data and 
          <span style={{
            backgroundColor: pass >= 2 ? theme.colors.accent : 'transparent',
            borderRadius: '4px',
            padding: '0 4px',
            transition: 'all 0.4s'
          }}> 
            semantic understanding 
          </span> 
          is built upon layers of cognitive scaffolding...
        </p>
        {/* Pass-driven Logic Blocks */}
        {pass === 1 && (
          <div style={{marginTop: '2rem', color: theme.colors.accent, fontStyle: 'italic'}}>
            [Lego-Assembly: 句法决策树已激活] - 识别谓语核心: "is built upon"
          </div>
        )}
      </main>

      {/* 认知支架侧边栏 */}
      <aside style={styles.sidebar}>
        <h3 style={{fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem'}}>
          Cognitive Support
        </h3>
        <div style={{fontSize: '0.9rem', color: theme.colors.ink}}>
          {pass === 0 && <p>Pass 1: 扫描全文，识别视觉锚点。</p>}
          {pass === 2 && (
            <div>
              <p>Pass 3: 120B 大模型实时解构中...</p>
              <div style={{height: '100px', width: '100%', backgroundColor: theme.colors.subtle, borderRadius: '8px', marginTop: '1rem'}} />
            </div>
          )}
        </div>
      </aside>
    </div>
  );
};

window.AIRMStudyLab = AIRMStudyLab;
