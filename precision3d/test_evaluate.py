"""对危险边界的必要验收：连续交叉、桥下、未知、动力学、到达后占位。"""
import copy,json,unittest
from build_tasks import baseline,rest_to_rest,task,world
from evaluate import evaluate
from acquire import ROOT,write_json

class SafetyChecks(unittest.TestCase):
    def test_synthetic_volumetric_underpass_fixture(self):
        t=task(1,.25,14);r=evaluate(t,world(14),baseline(t,'independent'));self.assertTrue(r['team_success'])
    def test_continuous_center_collision(self):
        t=task(2,.25,14);r=evaluate(t,world(14),baseline(t,'independent'));self.assertFalse(r['team_success']);self.assertLess(r['minimum_pair_distance_m'],1e-5)
    def test_serialized_pass(self):
        t=task(12,.4,14);r=evaluate(t,world(14),baseline(t,'serialized'));self.assertTrue(r['team_success'],r)
    def test_waiting_agent_near_departure_conflict(self):
        t=task(12,.6,14);r=evaluate(t,world(14),baseline(t,'serialized'));self.assertFalse(r['team_success']);self.assertTrue(any(x.startswith('PAIR_COLLISION') for x in r['failure_reasons']))
    def test_unknown_rejected(self):
        t=task(1,.25,14);w=world(14);w['free_boxes']=[];r=evaluate(t,w,baseline(t,'independent'));self.assertIn('uav_00:UNKNOWN_SPACE',r['failure_reasons'])
    def test_bridge_deck_collision(self):
        t=task(1,.25,14);t['agents'][0]['start'][2]=8.5;t['agents'][0]['goal'][2]=8.5;r=evaluate(t,world(14),baseline(t,'independent'));self.assertIn('uav_00:STATIC_COLLISION',r['failure_reasons'])
    def test_no_teleport(self):
        t=task(1,.25,14);s=baseline(t,'independent');s['trajectories']['uav_00'][1]['p'][0]+=1;self.assertEqual(evaluate(t,world(14),s)['status'],'INVALID')
    def test_speed_and_acceleration(self):
        t=task(1,.25,14);t['limits']['speed_mps']=1;t['limits']['acceleration_mps2']=1;r=evaluate(t,world(14),baseline(t,'independent'));self.assertIn('uav_00:SPEED',r['failure_reasons']);self.assertIn('uav_00:ACCELERATION',r['failure_reasons'])
    def test_missing_agent(self):
        t=task(2,.25,14);s=baseline(t,'independent');del s['trajectories']['uav_01'];self.assertEqual(evaluate(t,world(14),s)['status'],'INVALID')
    def test_nonfinite_rejected(self):
        t=task(1,.25,14);s=baseline(t,'independent');s['trajectories']['uav_00'][0]['p'][0]=float('nan');self.assertEqual(evaluate(t,world(14),s)['status'],'INVALID')
    def test_runtime_budget(self):
        t=task(1,.25,14);s=baseline(t,'independent');s['runtime_wall_s']=11;self.assertIn('RUNTIME_BUDGET',evaluate(t,world(14),s)['failure_reasons'])
    def test_model_scope_preserved(self):
        t=task(1,.25,14);w=world(14);w.update(unknown_policy='model_closed_world',free_boxes=[]);self.assertEqual(evaluate(t,w,baseline(t,'independent'))['status'],'PASS_MODEL_CONDITIONAL')
    def test_goal_remains_occupied(self):
        t=task(2,.25,14);t['agents'][1]['goal']=t['agents'][0]['goal'];s=baseline(t,'serialized');r=evaluate(t,world(14),s);self.assertTrue(any(x.startswith('PAIR_COLLISION') for x in r['failure_reasons']))

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SafetyChecks);r=unittest.TextTestRunner(verbosity=2).run(suite)
    write_json(ROOT/'evaluator_acceptance.json',dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),passed=r.wasSuccessful(),scope='Analytic quadratic trajectories and AABB geometry only'))
    raise SystemExit(not r.wasSuccessful())
