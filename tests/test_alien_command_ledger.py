import copy
import json
import unittest
from test_alien_command_portfolio import m, packet
from test_alien_command_plans import p


def with_ledger():
    data=packet()
    row={'missionId':101,'decisionReceiptId':7,'mission':'STR_ALIEN_HARVEST','region':'STR_NORTH_AFRICA','cost':3,
         'assignedAt':'1999-01-02 00:00:00','lastEventAt':'1999-01-29 00:00:00','gainAt':'1999-01-20 00:00:00',
         'coverage':'COMPLETE_FROM_ASSIGNMENT','lifecycle':'ENDED','outcome':'GAIN_VERIFIED','deliveryFact':'UNKNOWN',
         'cashEarned':2,'progressEarned':1,'deployed':2,'returned':1,'unavailable':1,'objectiveCarriers':1,
         'objectiveCarriersUnavailable':0,'evidenceTotal':3,'evidenceIds':[8,9,10]}
    data['operationLedger']={'schemaVersion':1,'asOf':'1999-02-01 00:00:00','total':1,'truncated':False,
        'lossWindowMonths':3,'regionalLosses':[{'region':'STR_NORTH_AFRICA','count':5,'evidenceIds':[9]}],
        'regionalLossesTruncated':False,'operations':[row]}
    return data


class OperationLedgerTests(unittest.TestCase):
    def test_gain_and_craft_loss_coexist_with_exact_parent_location(self):
        data=with_ledger();m.portfolio_input(data)
        captured=[]
        def choose(state,criteria,instructions):
            captured.append(json.loads(state));return 'SAVE',{}
        p.plan(data,choose,False,True)
        lessons=captured[0]['lessons']
        self.assertEqual(lessons['productive'],[['HARVEST','NORTH_AFRICA',1]])
        self.assertEqual(lessons['operations_cash_losses'][0][3:],[ 'GAIN_VERIFIED',2,1])
        self.assertEqual(lessons['resistance'],[['NORTH_AFRICA',0,5]])

    def test_rolling_losses_reach_target_packet_without_changing_current_sitrep(self):
        data=with_ledger();before=copy.deepcopy(data);captured=[]
        class Stop(Exception):pass
        def choose(state,criteria,instructions):
            if 'SAVE' in criteria:
                return next(k for k,v in criteria.items() if v.startswith('Harvest')),{}
            captured.append(json.loads(state));raise Stop()
        with self.assertRaises(Stop):p.plan(data,choose,False,True)
        self.assertIn(['NORTH_AFRICA',0,5],captured[0]['regions_reports_assignment_losses'])
        self.assertEqual(data,before)

    def test_prevention_requires_closed_complete_parent_and_all_carriers(self):
        data=with_ledger();row=data['operationLedger']['operations'][0]
        row.update(mission='STR_ALIEN_TERROR',cost=4,outcome='OBJECTIVE_PREVENTED',cashEarned=0,progressEarned=0,gainAt='',objectiveCarriersUnavailable=1)
        m.portfolio_input(data)
        for key,value in [('lifecycle','PENDING'),('coverage','PARTIAL_LEGACY'),('objectiveCarriersUnavailable',0),('deliveryFact','OBJECTIVE_SITE_DELIVERED')]:
            invalid=copy.deepcopy(data);invalid['operationLedger']['operations'][0][key]=value
            with self.assertRaises(ValueError):m.portfolio_input(invalid)

    def test_truncation_and_unverified_gains_rejected(self):
        for change in ({'outcome':'UNKNOWN'},{'cashEarned':4},{'gainAt':''}):
            data=with_ledger();data['operationLedger']['operations'][0].update(change)
            with self.assertRaises(ValueError):m.portfolio_input(data)
        data=with_ledger();data['operationLedger']['truncated']=True
        with self.assertRaises(ValueError):m.portfolio_input(data)

    def test_old_gain_not_reissued_as_current_month_productivity(self):
        data=with_ledger();data['operationLedger']['operations'][0]['gainAt']='1998-12-20 00:00:00'
        lessons=p.planner.campaign_lessons(data['budget'],[],data['sitrep'],data['operationLedger'])
        self.assertEqual(lessons['productive'],[])

    def test_rolling_clue_admits_search_with_receipt_support(self):
        data=with_ledger();data['knowledge']['candidates']=[{'mission':'STR_ALIEN_RETALIATION','region':r} for r in ('STR_NORTH_AFRICA','STR_ARCTIC')]
        result=p.plan(data,lambda s,c,i:(next(iter(c)),{}),False,True)
        self.assertEqual(result['operations'],[{'mission':'STR_ALIEN_RETALIATION','region':'STR_NORTH_AFRICA'}])
        self.assertIn(9,result['plans'][0]['supportIds'])


if __name__=='__main__':unittest.main()
