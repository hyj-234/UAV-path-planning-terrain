"""检查初筛会排除已观测危险，并且不会将几何通过升级为实机认证。"""
import json,unittest
import numpy as np
from screen_endpoints import CONFIG,ROOT,screen

def flat():
    x,y=np.meshgrid(np.arange(-2.4,2.401,.1),np.arange(-2.4,2.401,.1));p=np.column_stack((x.ravel(),y.ravel(),np.zeros(x.size)));return p,np.full(len(p),2)

class ScreeningChecks(unittest.TestCase):
    def test_flat_is_only_candidate(self):
        p,c=flat();r=screen(p,c,np.zeros(2),CONFIG);self.assertEqual(r['geometric_screen'],'GEOMETRY_CANDIDATE_ONLY');self.assertEqual(r['final_landing_status'],'UNQUALIFIED')
    def test_slope(self):
        p,c=flat();p[:,2]=.2*p[:,0];self.assertIn('SLOPE',screen(p,c,np.zeros(2),CONFIG)['exclusion_reasons'])
    def test_roughness(self):
        p,c=flat();p[:,2]=.3*np.sin(6*p[:,0]);self.assertIn('ROUGHNESS_RMS',screen(p,c,np.zeros(2),CONFIG)['exclusion_reasons'])
    def test_missing_ground(self):
        p,c=flat();c[:]=1;self.assertEqual(screen(p,c,np.zeros(2),CONFIG)['geometric_screen'],'INSUFFICIENT_GROUND_EVIDENCE')
    def test_missing_coverage(self):
        p,c=flat();keep=p[:,0]>0;self.assertIn('GROUND_COVERAGE',screen(p[keep],c[keep],np.zeros(2),CONFIG)['exclusion_reasons'])
    def test_vertical_obstacle(self):
        p,c=flat();p=np.vstack((p,[0,0,4]));c=np.append(c,6);self.assertIn('OBSERVED_VERTICAL_CORRIDOR_OBSTACLE',screen(p,c,np.zeros(2),CONFIG)['exclusion_reasons'])
    def test_hover_obstacle(self):
        p,c=flat();p=np.vstack((p,[0,0,8]));c=np.append(c,14);self.assertIn('OBSERVED_HOVER_OBSTACLE',screen(p,c,np.zeros(2),CONFIG)['exclusion_reasons'])
    def test_water(self):
        p,c=flat();p=np.vstack((p,[0,0,0]));c=np.append(c,9);self.assertIn('WATER_OBSERVATIONS',screen(p,c,np.zeros(2),CONFIG)['exclusion_reasons'])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ScreeningChecks))
    (ROOT/'screen_acceptance.json').write_text(json.dumps(dict(tests=result.testsRun,passed=result.wasSuccessful(),failures=len(result.failures),errors=len(result.errors)),indent=2),encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
