from pyrealb import *
from crmodel.model import *
import json
from geojson import Point, LineString, Feature, FeatureCollection, dumps

class CrDesc:

    def __init__(self):

        self.crossroad = None

    def loadModel(self, json_file):

        data = json.load(open(json_file))

        # Pedestrian Nodes
        pedestrian_nodes = {}
        for id in data["pedestrian_nodes"]:

            p = data["pedestrian_nodes"][id]

            if p["type"] == "Island":
                pedestrian_nodes[id] = Island(id)
            if p["type"] == "Sidewalk":
                pedestrian_nodes[id] = Sidewalk(id)

        # Junctions
        junctions = {}
        for id in data["junctions"]:

            j = data["junctions"][id]

            junctions[id] = Junction(id, j["x"], j["y"])
            if "Crosswalk" in j["type"]:
                junctions[id] = Crosswalk(
                    junctions[id], 
                    j["cw_tactile_paving"], 
                    [pedestrian_nodes[pn_id] for pn_id in j["pedestrian_nodes"]]
                )
            if "Traffic_light" in j["type"]:
                junctions[id] = Traffic_light(
                    junctions[id], 
                    j["tl_phase"], 
                    j["tl_direction"]
                )
            if "Pedestrian_traffic_light" in j["type"]:
                junctions[id] = Pedestrian_traffic_light(
                    junctions[id], 
                    j["ptl_sound"]
                )

        # Ways & channels
        ways = {}
        for id in data["ways"]:

            w = data["ways"][id]

            channels = []
            for channel in w["channels"]:
                if channel["type"] == "Bus":
                    channels.append(Bus(None, channel["direction"]))
                else:
                    channels.append(Road(None, channel["direction"]))

            ways[id] = Way(
                id, 
                w["name"], 
                [junctions[j_id] for j_id in w["junctions"]], 
                channels, 
                [pedestrian_nodes[p_id] if p_id else None for p_id in w["sidewalks"]], 
                [pedestrian_nodes[p_id] if p_id else None for p_id in w["islands"]]
            )

        # Branches
        branches = {}
        for id in data["branches"]:

            b = data["branches"][id]

            branches[id] = Branch(
                b["angle"],
                b["direction_name"],
                b["street_name"],
                [ways[w_id] for w_id in b["ways"]],
                id,
                Crossing(None, [junctions[c_id] for c_id in b["crossing"]["crosswalks"]])
            )

        self.crossroad = Intersection(None, branches.values(), data["center"])

    #
    # Text generation
    #
    # Returns : a dict with a text attribute containing the description, and a structure attribute containing the non-concatenated description
    #

    def generateDescription(self):

        # Load PyRealB french lexicon and add missing words
        loadFr()
        addToLexicon("pyramide", {"N":{"g":"f","tab":"n17"}})
        addToLexicon("croisement", {"N":{"g":"m","tab":"n3"}})
        addToLexicon("îlot", {"N":{"g":"m","tab":"n3"}})
        addToLexicon("tourne-à-gauche", {"N":{"g":"m","tab":"n3"}})
        addToLexicon("tourne-à-droite", {"N":{"g":"m","tab":"n3"}})
        addToLexicon("entrant", {"A":{"tab":"n28"}})
        addToLexicon("sortant", {"A":{"tab":"n28"}})

        # if a branch does not have a name, we name it "rue qui n'a pas de nom"
        for branch in self.crossroad.branches:
            if branch.street_name is None : branch.street_name = ["rue","qui n'a pas de nom"]

        #
        # General description
        #
        streets = []
        for branch in self.crossroad.branches:
            if branch.street_name not in streets : streets.append(branch.street_name) 
        s = CP(C("et"))
        for street in streets:
            s.add(
                PP(
                    P("de"), 
                    NP(
                        D("le"), 
                        N(street[0]), 
                        Q(street[1])
                    )
                )
            )
        general_desc = "Le carrefour à l'intersection %s est un carrefour à %s branches."%(s, len(self.crossroad.branches))

        #
        # Branches description
        #

        branches_desc = []
        for branch in self.crossroad.branches:

            # branch number
            number = NO(branch.number).dOpt({"nat": True})

            name = " ".join(branch.street_name)
            
            channels = []
            for way in branch.ways:
                channels += way.channels
            n_voies = PP(
                P("de"),
                NP(
                    NO(len(channels)).dOpt({"nat": True}), 
                    N("voie")
                )
            )
            # temporary fix for pyrealb issue 4 (https://github.com/lapalme/pyrealb/issues/4)
            if len(channels) == 8 : n_voies = "de huit voies"

            channels_in_desc = CP(C("et"))
            channels_out_desc = CP(C("et"))

            # count number of channels per type
            channels_in = {}
            channels_out = {}
            for channel in channels:

                c = None
                if channel.direction == "in":
                    c = channels_in
                else:
                    c = channels_out

                type = channel.__class__.__name__
                if type not in c:
                    c[type] = 0
                c[type] += 1

            n = None
            for type,n in channels_in.items():
                channels_in_desc.add(
                    NP(
                        NO(n).dOpt({"nat": True}),
                        N("voie"),
                        PP(
                            P("de"),
                            N(tr(type))
                        )
                    )
                )
            if channels_in:
                word = "entrante"
                
                if n > 1:
                    word += "s"
                channels_in_desc = "%s %s"%(channels_in_desc, word)

            for type,n in channels_out.items():
                channels_out_desc.add(
                    NP(
                        NO(n).dOpt({"nat": True}),
                        N("voie"),
                        PP(
                            P("de"),
                            N(tr(type))
                        )
                    )
                )
            if channels_out:
                word = "sortante"
                if n > 1:
                    word += "s"
                channels_out_desc = "%s %s"%(channels_out_desc, word)

            branch_desc = "La branche numéro %s qui s'appelle %s est composée %s : %s%s%s."%(number, name, n_voies, channels_out_desc, ", et " if channels_in and channels_out else "", channels_in_desc)

            # post process to remove ':' and duplicate information if there's only one type of way in one direction
            branch_desc = branch_desc.split(" ")
            if " et " not in branch_desc:
                i = branch_desc.index(":")
                if branch_desc[i-2] == "d'une": branch_desc[i+1] = "d'une"
                branch_desc.pop(i-2)
                branch_desc.pop(i-2)
                branch_desc.pop(i-2)
            branch_desc = " ".join(branch_desc)

            # hacks to prettify sentences
            branch_desc = branch_desc.replace("qui s'appelle rue qui n'a pas de nom", "qui n'a pas de nom")
            branch_desc = branch_desc.replace("de une voie", "d'une voie")
            
            branches_desc.append(branch_desc)

        #
        # Traffic light cycle
        # right turn on red are barely modelized in OSM, see https://wiki.openstreetmap.org/w/index.php?title=Red_turn&oldid=2182526
        #

        #TODO

        #
        # Attention points
        #

        # TODO

        #
        # Crossings descriptions
        #
        crossings_desc = []

        for branch in self.crossroad.branches:

            number = NO(branch.number).dOpt({"nat": True})

            name = " ".join(branch.street_name)
            crosswalks = branch.crossing.crosswalks if branch.crossing is not None else []

            crossing_desc = ""
            if len(crosswalks):

                n_crosswalks = NP(NO(len(crosswalks)).dOpt({"nat": True})).g("f") # followed by "fois", which is f.
                n_podotactile = 0
                n_ptl = 0
                n_ptl_sound = 0
                incorrect = False
                for crosswalk in crosswalks:
                    if crosswalk.cw_tactile_paving != "no":
                        n_podotactile += 1
                    if crosswalk.cw_tactile_paving == "incorrect":
                        incorrect = True
                    if "Pedestrian_traffic_light" in crosswalk.type:
                        n_ptl += 1
                        if crosswalk.ptl_sound == "yes":
                            n_ptl_sound += 1

                crossing_desc = "Les passages piétons "
                if n_ptl:
                    if n_ptl == len(crosswalks):
                        crossing_desc += "sont tous protégés par un feu. "
                    else :
                        crossing_desc += "ne sont pas tous protégés par un feu. "
                else:
                    crossing_desc += "ne sont pas protégés par des feux. "
                    
                
                if n_podotactile:
                    if n_podotactile == len(crosswalks) and incorrect == False:
                        crossing_desc += "Il y a des bandes d'éveil de vigilance."
                    else:
                        crossing_desc += "Il manque des bandes d'éveil de vigilance ou celles-ci sont dégradées."
                else:
                    crossing_desc += "Il n'y a pas de bandes d'éveil de vigilance."
                
            crossings_desc.append("La branche numéro %s %s. %s"%(number, "se traverse en %s fois"%n_crosswalks if len(crosswalks) else "ne se traverse pas", crossing_desc))

        #
        # Print description
        #

        description = ""
        description += general_desc+"\n\n"

        description += "== Description des branches ==\n\n"

        for branch_desc in branches_desc:
            description += branch_desc+"\n\n"

        description += "== Description des traversées ==\n\n"

        for crossing_desc in crossings_desc:
            description += crossing_desc+"\n\n"

        return({'text' : description, 'structure' : {'general_desc' : general_desc, 'branches_desc' : branches_desc, 'crossings_desc' : crossings_desc}})

    #
    # Generate a JSON that bind generated descriptions to OSM nodes
    #
    # Dependencies : the non-concatenated description
    # Returns : the JSON as a string

    def descriptionToJSON(self, description_structure):

        data = {}
        general_desc = description_structure["general_desc"]
        branches_desc = description_structure["branches_desc"]
        crossings_desc = description_structure["crossings_desc"]
        branches = self.crossroad.branches
        junctions = self.crossroad.junctions
        
        data["introduction"] = general_desc
        
        data["branches"] = []
        for (branch, branch_desc, crossing_desc) in zip(branches, branches_desc, crossings_desc):
            crossing_desc = crossing_desc.split(" ")[4:]
            crossing_desc.insert(0, "Elle")
            nodes = []
            for way in branch.ways:
                nodes.append([junction.id for junction in way.junctions])
            data["branches"].append({
                "nodes" : nodes,
                "text" : branch_desc + " " + " ".join(crossing_desc),
                "tags" : {
                    "auto" : "yes"
                }
            })
        
        crosswalks = []
        for junction in junctions.values():
            if "Crosswalk" in junction.type:
                crosswalks.append(junction)

        data["crossings"] = []
        for crosswalk in crosswalks:
            crosswalk_desc = "Le passage piéton "

            if "Pedestrian_traffic_light" in crosswalk.type:
                crosswalk_desc += "est protégé par un feu"
                if crosswalk.ptl_sound == "yes":
                    crosswalk_desc += " sonore. "
                else :
                    crosswalk_desc += ". "
            else:
                crosswalk_desc += "n'est pas protégé par un feu. "

            if crosswalk.cw_tactile_paving == "yes":
                crosswalk_desc += "Il y a des bandes d'éveil de vigilance."
            elif crosswalk.cw_tactile_paving == "incorrect":
                crosswalk_desc += "Il manque des bandes d'éveil de vigilance ou celles-ci sont dégradées."
            else:
                crosswalk_desc += "Il n'y a pas de bandes d'éveil de vigilance."

            data["crossings"].append({
                "node" : crosswalk.id,
                "text" : crosswalk_desc,
                "tags" : {
                    "auto" : "yes"
                }
            })

        return(json.dumps(data, ensure_ascii=False))

    def getGeoJSON(self, description_structure):
        features = []

        # Crossroad general description
        features.append(Feature(geometry=Point([self.crossroad.center["x"], self.crossroad.center["y"]]), properties={
            "id" : None,
            "type" : "crossroads",
            "description" : description_structure["general_desc"]
        }))

        # Crossroad branch description
        branches_ways = []
        for (branch, branch_desc) in zip(self.crossroad.branches, description_structure["branches_desc"]):
            for way in branch.ways:
                n1 = way.junctions[0]
                n2 = way.junctions[1]
                features.append(Feature(geometry=LineString([(n1.x, n1.y), (n2.x, n2.y)]), properties={
                    "id" : "%s;%s"%(n1.id, n2.id),
                    "type" : "branch",
                    "name" : "branch n°%s | %s"%(branch.number,way.name),
                    "description" : branch_desc,
                    "left_sidewalk" : way.sidewalks[0].id if way.sidewalks[0] else "",
                    "right_sidewalk" : way.sidewalks[1].id if way.sidewalks[1] else "",
                    "left_island" : way.islands[0].id if way.islands[0] else "",
                    "right_island" : way.islands[1].id if way.islands[1] else ""
                }))
                branches_ways.append(way)
        
        # Crossroad ways
        for way in self.crossroad.ways.values():
            if way not in branches_ways:
                n1 = way.junctions[0]
                n2 = way.junctions[1]
                features.append(Feature(geometry=LineString([(n1.x, n1.y), (n2.x, n2.y)]), properties={
                    "id" : "%s;%s"%(n1.id, n2.id),
                    "type" : "way",
                    "name" : way.name,
                    "left_sidewalk" : way.sidewalks[0].id if way.sidewalks[0] else "",
                    "right_sidewalk" : way.sidewalks[1].id if way.sidewalks[1] else "",
                    "left_island" : way.islands[0].id if way.islands[0] else "",
                    "right_island" : way.islands[1].id if way.islands[1] else ""
                }))

        # Single crosswalks descriptions
        crosswalks = []
        for junction in self.crossroad.junctions.values():
            if "Crosswalk" in junction.type:
                crosswalks.append(junction)
        for crosswalk in crosswalks:
            crosswalk_desc = "Le passage piéton "

            if "Pedestrian_traffic_light" in crosswalk.type:
                crosswalk_desc += "est protégé par un feu"
                if crosswalk.ptl_sound == "yes":
                    crosswalk_desc += " sonore. "
                else :
                    crosswalk_desc += ". "
            else:
                crosswalk_desc += "n'est pas protégé par un feu. "

            if crosswalk.cw_tactile_paving == "yes":
                crosswalk_desc += "Il y a des bandes d'éveil de vigilance."
            elif crosswalk.cw_tactile_paving == "incorrect":
                crosswalk_desc += "Il manque des bandes d'éveil de vigilance ou celles-ci sont dégradées."
            else:
                crosswalk_desc += "Il n'y a pas de bandes d'éveil de vigilance."
            features.append(Feature(geometry=Point([crosswalk.x, crosswalk.y]), properties={
                "id" : crosswalk.id,
                "type" : "crosswalk",
                "description" : crosswalk_desc
            }))

        # Crossings description
        for crossing, crossing_desc in zip([branch.crossing for branch in self.crossroad.branches], description_structure["crossings_desc"]):
            if crossing is None:
                continue
            crosswalks = crossing.crosswalks
            geom = None
            id = None
            if len(crosswalks) > 1:
                id = ";".join(map(str,[crosswalks[i].id for i in range(len(crosswalks))]))
                geom = LineString([(crosswalks[i].x, crosswalks[i].y) for i in range(len(crosswalks))])
            else:
                id = crosswalks[0].id
                geom = Point([crosswalks[0].x, crosswalks[0].y])
            features.append(Feature(geometry=geom, properties={
                "id" : id,
                "type" : "crossing",
                "description" : crossing_desc
            }))

        return(dumps(FeatureCollection(features)))