<script>
export default {
  onLaunch: function() {
    console.log('EPI-Vision App launched');
  },
  onShow: function() {
    console.log('EPI-Vision App show');
  },
  onHide: function() {
    console.log('EPI-Vision App hide');
  }
};
</script>

<style>
/* Global styles */
page {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #020617;
  color: #f8fafc;
}

/* Theme system - CSS variables on :root */
:root {
  --accent-primary: #0ea5e9;
  --accent-primary-glow: rgba(14, 165, 233, 0.3);
  --accent-secondary: #8b5cf6;
  --accent-success: #10b981;
  --accent-warning: #f59e0b;
  --accent-danger: #e11d48;
  --bg-card: rgba(15, 23, 42, 0.6);
  --bg-input: rgba(15, 23, 42, 0.8);
  --border-color: rgba(51, 65, 85, 0.4);
  --border-glow: rgba(56, 189, 248, 0.15);
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #475569;
}
</style>
